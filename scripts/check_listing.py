"""Checks a pull request that changes the plugin or theme list, as far as a script can.

Compares the files at <head> with the files at the merge base of <base> and <head>, and checks only
what the pull request changed. The zips of new versions are downloaded and read with the same rules
as Hindsight. Prints a Markdown report: the problems, which must be fixed, and what the reviewer
still checks by hand. Exits with 1 if there are problems.

Usage: python3 check_listing.py <base> <head> [--author <GitHub account>]
<base> and <head> are git revisions, such as FETCH_HEAD and HEAD. The files are read with git, so
nothing in them runs. --author is the account that opened the pull request. If the environment
variable GITHUB_TOKEN is set, the GitHub API requests use it.
"""

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import unicodedata
import urllib.request
import zipfile
import zlib
from urllib.parse import quote, urlparse

from build_themes import (
    ID,
    MAX_CSS_BYTES,
    MAX_JSON_BYTES,
    MAX_ZIP_BYTES as MAX_THEME_ZIP_BYTES,
    SCHEMA_URL,
    THEMES_JSON_FORMAT_VERSION,
    ThemeError,
    fetch_public_tokens,
    read_file,
)
from count_downloads import (
    PLUGINS_JSON_FORMAT_VERSION,
    fetch_assets,
    fetch_with_retries,
    parse_url,
)

LIST_FILES = ("plugins.json", "themes.json")
ICONS = "icons/"

# A plugin whose repository is under this account is official
OFFICIAL_ACCOUNT = "Tomotsugu-dev"

# The interface languages of Hindsight
LANGUAGES = ("zh-CN", "zh-TW", "en", "ja", "pt-BR", "es")

VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
SHA256 = re.compile(r"[0-9a-fA-F]{64}")
REPO = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+")

# The rules below are copied from Hindsight 0.10.3. When Hindsight changes one, change it here too.

# src-tauri/src/plugins/manifest.rs: each permission, and the permission it must be requested with
PERMISSIONS = {
    "stats.read": None,
    "stats.today": "stats.read",
    "stats.week": "stats.read",
    "stats.month": "stats.read",
    "stats.history": "stats.read",
    "devices.read": None,
    "categories.read": None,
    "super_categories.read": None,
    "notifications": None,
    "notifications.sound": "notifications",
    "island": None,
    "focus.changed": None,
    "focus.app": "focus.changed",
    "focus.category": "focus.changed",
    "focus.title": "focus.changed",
}
MAX_STORAGE_MB = 10 * 1024
OPENS_IN = ("main", "window")
MIN_WINDOW_SIDE = 200
MAX_WINDOW_WIDTH = 2560
MAX_WINDOW_HEIGHT = 1440

# src-tauri/src/plugins/market.rs, install.rs and icon.rs
MAX_PLUGIN_ZIP_BYTES = 500 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
MAX_ENTRIES = 1000
MAX_UNPACKED_BYTES = 100 * 1024 * 1024
ICON = "icon.png"
MAX_ICON_BYTES = 256 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# src-tauri/src/themes/plugin/manifest.rs
MAX_TEXT_CHARS = 64
MAX_TOKEN_VALUE_CHARS = 300

# CSS functions that load a file. url() and src() take the address. The others take an address as
# a string, or a url()
CSS_ESCAPE = re.compile(r"\\([0-9a-fA-F]{1,6})[ \t\r\n\f]?|\\(.)", re.S)
CSS_ADDRESS = re.compile(r"(?<![\w-])(?:url|src)\(\s*['\"]?", re.I)
CSS_STRING_ADDRESS = re.compile(
    r"(?<![\w-])(?:-webkit-image-set|image-set|image|cross-fade)\(", re.I
)
CSS_STRING = re.compile(r"\"([^\"]*)\"|'([^']*)'")


class Problem(Exception):
    """Something the pull request must fix. The message goes into the report."""


class Report:
    def __init__(self):
        self.problems = []
        self.notes = []

    def markdown(self):
        lines = ["## Listing check", ""]
        if self.problems:
            lines += ["### Fix these", ""] + [f"- {p}" for p in self.problems] + [""]
        else:
            lines += ["The script found no problems.", ""]
        if self.notes:
            lines += ["### For the reviewer", ""] + [f"- {n}" for n in self.notes] + [""]
        return "\n".join(lines)


def code(value):
    """Shows a value from the pull request in the report as code.

    In code, Markdown does not make links, images or @mentions.
    """
    text = str(value).replace("`", "'").replace("\n", " ")
    if len(text) > 100:
        text = text[:100] + "…"
    return f"`{text}`"


def check(base, head, github, author=None):
    """Checks what changed from base to head. Returns a Report.

    base and head are {path: contents} of the files in the repository. github has
    fetch_assets(repo), download(url, limit) and public_tokens(), like GitHub below.
    """
    report = Report()
    changed = {path for path in base.keys() | head.keys() if base.get(path) != head.get(path)}
    others = sorted(p for p in changed if p not in LIST_FILES and not p.startswith(ICONS))
    if others:
        report.problems.append(
            "Only plugins.json, themes.json and icons/ can change in a listing pull request. "
            f"Move these changes to another pull request: {', '.join(code(p) for p in others)}"
        )
    if "plugins.json" in changed or any(p.startswith(ICONS) for p in changed):
        check_plugins(base, head, changed, github, author, report)
    if "themes.json" in changed:
        check_themes(base, head, github, author, report)
    if not changed:
        report.notes.append("Nothing changed.")
    return report


def read_list(files, file_name, key, format_version):
    """Reads plugins.json or themes.json from files. Returns the list under key."""
    if file_name not in files:
        raise Problem(f"{file_name} is missing")
    try:
        file = json.loads(files[file_name].decode("utf-8"))
    except ValueError as e:
        raise Problem(f"{file_name} is not valid JSON: {e}") from e
    if not isinstance(file, dict) or file.get("format_version") != format_version:
        raise Problem(f"`format_version` in {file_name} must be {format_version}")
    if not isinstance(file.get(key), list):
        raise Problem(f"`{key}` in {file_name} must be a list")
    return file[key]


def read_old_list(files, file_name, key, format_version):
    """Reads the list at the merge base. Returns {id: entry}, or {} if it cannot be read."""
    try:
        entries = read_list(files, file_name, key, format_version)
    except Problem:
        return {}
    return {e["id"]: e for e in entries if isinstance(e, dict) and isinstance(e.get("id"), str)}


def check_ids(entries, file_name, report):
    """Reports ids that are used more than once. Returns the ids."""
    ids = [e.get("id") for e in entries if isinstance(e, dict)]
    for i in sorted({i for i in ids if ids.count(i) > 1}, key=str):
        report.problems.append(f"{code(i)} is used by more than one entry in {file_name}")
    return ids


def version_key(version):
    return tuple(int(n) for n in version.split("."))


def check_plugins(base, head, changed, github, author, report):
    try:
        plugins = read_list(head, "plugins.json", "plugins", PLUGINS_JSON_FORMAT_VERSION)
    except Problem as e:
        report.problems.append(str(e))
        return
    old = read_old_list(base, "plugins.json", "plugins", PLUGINS_JSON_FORMAT_VERSION)
    ids = check_ids(plugins, "plugins.json", report)
    for i, plugin in enumerate(plugins):
        if not isinstance(plugin, dict):
            report.problems.append(f"Entry {i} in plugins.json is not an object")
            continue
        icon_path = f"{ICONS}{plugin.get('id')}.png"
        previous = old.get(plugin.get("id"))
        if plugin == previous and icon_path not in changed:
            continue
        icon = head.get(icon_path)
        check_plugin(plugin, previous, icon, icon_path in changed, github, author, report)
    for plugin_id in old:
        if plugin_id not in ids:
            report.notes.append(f"Removes the plugin {code(plugin_id)}.")
    for path in sorted(p for p in changed if p.startswith(ICONS) and p in head):
        if path.removeprefix(ICONS).removesuffix(".png") not in ids:
            report.problems.append(f"{code(path)} is not the icon of a plugin in plugins.json")


def plugin_problems(plugin):
    """Returns what breaks the rules in one entry of plugins.json, without the network."""
    problems = []
    if not isinstance(plugin.get("id"), str) or not ID.fullmatch(plugin["id"]):
        problems.append(
            "`id` must be 1 to 63 lowercase letters, digits and -, and cannot start or end with -"
        )
    for key in ("name", "author"):
        if not isinstance(plugin.get(key), str) or not plugin[key].strip():
            problems.append(f"`{key}` must be a text that is not empty")
    description = plugin.get("description")
    if not is_text_map(description):
        problems.append("`description` must map language codes to texts")
    else:
        unknown = [k for k in description if k not in LANGUAGES]
        if unknown:
            problems.append(
                f"`description` has unknown language codes {', '.join(code(k) for k in unknown)}. "
                f"Use {', '.join(LANGUAGES)}"
            )
        if "en" not in description:
            problems.append("`description` must have `en`")
    repo = plugin.get("repo")
    if not isinstance(repo, str) or not REPO.fullmatch(repo):
        problems.append("`repo` must be `owner/name`")
        repo = None
    versions = plugin.get("versions")
    if not isinstance(versions, list) or not versions:
        problems.append("`versions` must be a list that is not empty")
        return problems
    seen = set()
    for i, version in enumerate(versions):
        if not isinstance(version, dict):
            problems.append(f"version {i} is not an object")
            continue
        name = version.get("version")
        label = code(name) if isinstance(name, str) else f"version {i}"
        if not isinstance(name, str) or not VERSION.fullmatch(name):
            problems.append(f"{label}: `version` must be three numbers, such as `0.1.0`")
        elif name in seen:
            problems.append(f"{label} is listed twice")
        seen.add(name)
        problems += [f"{label}: {p}" for p in url_problems(version, repo)]
        permissions = version.get("permissions")
        if not isinstance(permissions, list) or not all(isinstance(p, str) for p in permissions):
            problems.append(f"{label}: `permissions` must be a list of texts")
        else:
            problems += [f"{label}: {p}" for p in permission_problems(permissions)]
        if "storage_mb" in version and not is_storage_mb(version["storage_mb"]):
            problems.append(f"{label}: {STORAGE_MB_RULE}")
    return problems


def url_problems(version, repo):
    """Checks url and sha256 of a version in plugins.json or themes.json."""
    problems = []
    url = version.get("url")
    parsed = parse_url(url) if isinstance(url, str) else None
    if parsed is None:
        problems.append("`url` must be a file in a GitHub release")
    elif repo is not None and parsed[0] != repo.lower():
        problems.append(f"`url` must be a release file of {code(repo)}")
    if not isinstance(version.get("sha256"), str) or not SHA256.fullmatch(version["sha256"]):
        problems.append("`sha256` must be 64 hexadecimal digits")
    return problems


def permission_problems(permissions):
    """The permission rules of Hindsight."""
    problems = []
    for p in permissions:
        if p not in PERMISSIONS:
            problems.append(f"unknown permission {code(p)}")
        elif PERMISSIONS[p] is not None and PERMISSIONS[p] not in permissions:
            problems.append(f"`{p}` needs `{PERMISSIONS[p]}`")
    # The install dialog shows how far back the plugin can read, so stats.read needs a range
    ranges = [name for name, needs in PERMISSIONS.items() if needs == "stats.read"]
    if "stats.read" in permissions and not any(r in permissions for r in ranges):
        problems.append(f"`stats.read` needs one of {', '.join(ranges)}")
    return problems


STORAGE_MB_RULE = f"`storage_mb` must be a whole number from 1 to {MAX_STORAGE_MB}"


def is_storage_mb(value):
    # In Python, True is also an int
    return type(value) is int and 1 <= value <= MAX_STORAGE_MB


def is_text_map(value):
    return isinstance(value, dict) and all(isinstance(v, str) for v in value.values())


def check_plugin(plugin, previous, icon, icon_changed, github, author, report):
    """Checks one plugin that the pull request added or changed."""
    plugin_id = plugin.get("id")
    problems = plugin_problems(plugin)
    if problems:
        report.problems += [f"{code(plugin_id)}: {p}" for p in problems]
        return
    repo = plugin["repo"]
    owner = repo.split("/")[0]
    old_versions = {v["version"]: v for v in previous["versions"]} if previous else {}
    versions = sorted(plugin["versions"], key=lambda v: version_key(v["version"]))
    names = [v["version"] for v in versions]

    if previous is not None and previous.get("repo") != repo:
        report.notes.append(
            f"{code(plugin_id)} moves from {code(previous.get('repo'))} to {code(repo)}."
        )
    if author is not None and author.lower() != owner.lower():
        report.notes.append(
            f"{code(author)} opened this pull request, but {code(repo)} is under {code(owner)}. "
            "Check that the owner agreed."
        )
    for name in old_versions:
        if name not in names:
            report.notes.append(f"Removes {code(plugin_id)} {code(name)}.")

    icons_in_zips = {}
    for version in versions:
        name = version["version"]
        label = f"{code(plugin_id)} {code(name)}"
        old = old_versions.get(name)
        if old is not None:
            for key in ("url", "sha256", "permissions", "storage_mb"):
                if old.get(key) != version.get(key):
                    report.problems.append(f"{label} {already_listed(key)}")
            continue
        try:
            manifest, icons_in_zips[name] = check_plugin_release(plugin, version, github)
        except (Problem, ThemeError, OSError) as e:
            report.problems.append(f"{label}: {e}")
            continue
        if name == names[-1] and manifest["name"] != plugin["name"]:
            report.problems.append(
                f"{label}: `name` is {code(plugin['name'])}, but the manifest has "
                f"{code(manifest['name'])}. Use the name in the manifest"
            )

    # The reviewer looks at the newest new version only, and compares it with the newest listed one
    new = [v for v in versions if v["version"] not in old_versions]
    listed = [v for v in versions if v["version"] in old_versions]
    if new:
        latest = new[-1]
        label = f"{code(plugin_id)} {code(latest['version'])}"
        if previous is None:
            if owner.lower() != OFFICIAL_ACCOUNT.lower():
                report.notes.append(
                    f"{code(plugin_id)} is a third-party plugin. Read its code: "
                    f"https://github.com/{repo}/tree/{tag_of(latest)}"
                )
            permissions = ", ".join(latest["permissions"]) or "none"
            report.notes.append(
                f"{label} asks for these permissions: {permissions}. "
                f"Storage: {latest.get('storage_mb', 'none')} MB."
            )
        elif listed:
            note_new_version(plugin, listed[-1], latest, report)
        report.notes.append(f"Install {label} and try it.")

    # The market shows icons/<id>.png, and the installed plugin shows icon.png of the newest version
    newest = versions[-1]
    label = f"{code(plugin_id)} {code(newest['version'])}"
    if newest["version"] not in icons_in_zips:
        # A new version that is not in icons_in_zips failed, and is already in the report
        if not icon_changed or newest["version"] not in old_versions:
            return
        try:
            _, icons_in_zips[newest["version"]] = check_plugin_release(plugin, newest, github)
        except (Problem, ThemeError, OSError) as e:
            report.problems.append(f"{label}: {e}")
            return
    in_zip = icons_in_zips[newest["version"]]
    icon_path = code(f"{ICONS}{plugin_id}.png")
    if in_zip is None and icon is not None:
        report.problems.append(f"{label}: the zip has no {ICON}, so remove {icon_path}")
    elif in_zip is not None and icon is None:
        report.problems.append(f"{label}: add {icon_path}, the same file as {ICON} in the zip")
    elif in_zip != icon:
        report.problems.append(f"{label}: {icon_path} must be the same file as {ICON} in the zip")


def note_new_version(plugin, older, version, report):
    """Tells the reviewer what changed from an older listed version."""
    label = f"{code(plugin['id'])} {code(version['version'])}"
    added = [p for p in version["permissions"] if p not in older["permissions"]]
    if added:
        report.notes.append(f"{label} asks for new permissions: {', '.join(added)}.")
    if version.get("storage_mb", 0) > older.get("storage_mb", 0):
        report.notes.append(
            f"{label} asks for {version['storage_mb']} MB, {code(older['version'])} for "
            f"{older.get('storage_mb', 0)} MB."
        )
    report.notes.append(
        f"Code changes since {code(older['version'])}: "
        f"https://github.com/{plugin['repo']}/compare/{tag_of(older)}...{tag_of(version)}"
    )


def tag_of(version):
    """The release tag of the version, ready to put in a link."""
    return quote(parse_url(version["url"])[1], safe="")


def already_listed(key):
    return f"is already listed, so its `{key}` cannot change. List a new version instead"


def check_release(version, github, limit):
    """Checks that the release file is the zip in the list, and downloads it. Returns the zip."""
    repo, tag, name = parse_url(version["url"])
    sha256 = version["sha256"].lower()
    asset = github.fetch_assets(repo).get((tag, name))
    if asset is None:
        raise Problem(f"{code(name)} is not in the latest 100 releases of {code(repo)}")
    if asset["digest"] is not None and asset["digest"] != f"sha256:{sha256}":
        raise Problem("the zip in the release does not match `sha256`")
    data = github.download(version["url"], limit)
    if len(data) > limit:
        raise Problem(f"the zip is larger than {limit // 1024 // 1024} MB")
    if hashlib.sha256(data).hexdigest() != sha256:
        raise Problem("the downloaded zip does not match `sha256`")
    return data


def check_plugin_release(plugin, version, github):
    """Downloads a new version and checks its zip against the list. Returns (manifest, icon)."""
    data = check_release(version, github, MAX_PLUGIN_ZIP_BYTES)
    manifest, icon = read_plugin_zip(data)
    if manifest["id"] != plugin["id"]:
        raise Problem(f"the manifest has the id {code(manifest['id'])}")
    if manifest["version"] != version["version"]:
        raise Problem(f"the manifest has the version {code(manifest['version'])}")
    if sorted(manifest["permissions"]) != sorted(version["permissions"]):
        permissions = ", ".join(manifest["permissions"]) or "none"
        raise Problem(f"`permissions` must be the same as in the manifest: {permissions}")
    if manifest.get("storage_mb") != version.get("storage_mb"):
        raise Problem(
            "`storage_mb` must be the same as in the manifest: "
            f"{manifest.get('storage_mb', 'none')}"
        )
    return manifest, icon


def read_plugin_zip(data):
    """Checks a plugin zip as Hindsight installs it. Returns (manifest, icon.png or None)."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = z.infolist()
            if len(infos) > MAX_ENTRIES:
                raise Problem(f"the zip has more than {MAX_ENTRIES} entries")
            for info in infos:
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise Problem(f"the zip has a symlink, {code(info.filename)}")
                if not is_enclosed(info.filename):
                    raise Problem(f"the zip has an unsafe path, {code(info.filename)}")
            unpacked = 0
            for info in infos:
                if info.is_dir():
                    continue
                # Count the bytes that are read: the sizes written in the zip can be false
                with z.open(info) as f:
                    while chunk := f.read(1024 * 1024):
                        unpacked += len(chunk)
                        if unpacked > MAX_UNPACKED_BYTES:
                            raise Problem("the zip is larger than 100 MB unpacked")
            manifest_json = read_file(z, "manifest.json", MAX_MANIFEST_BYTES)
            icon = read_file(z, ICON, MAX_ICON_BYTES)
            names = set(z.namelist())
    # Not a zip, broken contents, a compression method that is not supported, or a password
    except (zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError) as e:
        raise Problem(f"the zip cannot be read: {e}") from e
    if manifest_json is None:
        raise Problem("the zip has no manifest.json")
    if icon is not None and not icon.startswith(PNG_SIGNATURE):
        raise Problem(f"{ICON} is not a PNG file")
    manifest = parse_manifest(manifest_json)
    if manifest["runs_in_background"] and "background.js" not in names:
        raise Problem("the manifest has `runs_in_background`, but the zip has no background.js")
    return manifest, icon


def is_enclosed(path):
    """Returns whether the path stays in the folder it is unpacked into, on Windows too."""
    if "\0" in path or path.startswith(("/", "\\")) or re.match(r"[A-Za-z]:", path):
        return False
    depth = 0
    for part in re.split(r"[/\\]", path):
        if part == "..":
            depth -= 1
            if depth < 0:
                return False
        elif part not in ("", "."):
            depth += 1
    return True


def parse_manifest(data):
    """Reads manifest.json with the rules of Hindsight. Returns it as a dict."""
    try:
        manifest = json.loads(data.decode("utf-8"))
    except ValueError as e:
        raise Problem(f"manifest.json is not valid JSON: {e}") from e
    if not isinstance(manifest, dict):
        raise Problem("manifest.json is not a JSON object")
    for key in ("id", "name", "version"):
        if not isinstance(manifest.get(key), str):
            raise Problem(f"manifest.json: `{key}` must be a text")
    permissions = manifest.get("permissions")
    if not isinstance(permissions, list) or not all(isinstance(p, str) for p in permissions):
        raise Problem("manifest.json: `permissions` must be a list of texts")
    if not isinstance(manifest.get("runs_in_background"), bool):
        raise Problem("manifest.json: `runs_in_background` must be true or false")
    if not ID.fullmatch(manifest["id"]):
        raise Problem(f"manifest.json: invalid id {code(manifest['id'])}")
    if not VERSION.fullmatch(manifest["version"]):
        raise Problem(f"manifest.json: invalid version {code(manifest['version'])}")
    if not manifest["name"].strip():
        raise Problem("manifest.json: `name` is empty")
    opens_in = manifest.get("opens_in")
    if opens_in is not None and opens_in not in OPENS_IN:
        raise Problem(f"manifest.json: `opens_in` must be {' or '.join(OPENS_IN)}")
    window = manifest.get("window")
    if window is not None:
        width = window.get("width") if isinstance(window, dict) else None
        height = window.get("height") if isinstance(window, dict) else None
        if not (
            type(width) is int
            and type(height) is int
            and MIN_WINDOW_SIDE <= width <= MAX_WINDOW_WIDTH
            and MIN_WINDOW_SIDE <= height <= MAX_WINDOW_HEIGHT
        ):
            raise Problem(
                f"manifest.json: `window` must be {MIN_WINDOW_SIDE}x{MIN_WINDOW_SIDE} to "
                f"{MAX_WINDOW_WIDTH}x{MAX_WINDOW_HEIGHT}"
            )
    problems = permission_problems(permissions)
    if problems:
        raise Problem(f"manifest.json: {problems[0]}")
    if "focus.changed" in permissions and not manifest["runs_in_background"]:
        raise Problem("manifest.json: `focus.changed` needs `runs_in_background`")
    if manifest.get("storage_mb") is None:
        manifest.pop("storage_mb", None)
    elif not is_storage_mb(manifest["storage_mb"]):
        raise Problem(f"manifest.json: {STORAGE_MB_RULE}")
    return manifest


def check_themes(base, head, github, author, report):
    try:
        themes = read_list(head, "themes.json", "themes", THEMES_JSON_FORMAT_VERSION)
    except Problem as e:
        report.problems.append(str(e))
        return
    old = read_old_list(base, "themes.json", "themes", THEMES_JSON_FORMAT_VERSION)
    ids = check_ids(themes, "themes.json", report)
    for i, theme in enumerate(themes):
        if not isinstance(theme, dict):
            report.problems.append(f"Entry {i} in themes.json is not an object")
        elif theme != old.get(theme.get("id")):
            check_theme(theme, old.get(theme.get("id")), github, author, report)
    for theme_id in old:
        if theme_id not in ids:
            report.notes.append(f"Removes the theme {code(theme_id)}.")


def theme_problems(theme):
    """Returns what breaks the rules in one entry of themes.json, without the network."""
    problems = []
    theme_id = theme.get("id")
    # The website uses the id as a file name, and index would be the same name as index.json
    if not isinstance(theme_id, str) or not ID.fullmatch(theme_id) or theme_id == "index":
        problems.append(
            "`id` must be 1 to 63 lowercase letters, digits and -, cannot start or end with -, "
            "and cannot be `index`"
        )
    repo = theme.get("repo")
    if not isinstance(repo, str) or not REPO.fullmatch(repo):
        problems.append("`repo` must be `owner/name`")
        repo = None
    if "homepage" in theme:
        homepage = theme["homepage"]
        parsed = urlparse(homepage) if isinstance(homepage, str) else None
        if parsed is None or parsed.scheme != "https" or not parsed.netloc:
            problems.append("`homepage` must start with `https://`")
    versions = theme.get("versions")
    if not isinstance(versions, list) or not versions:
        problems.append("`versions` must be a list that is not empty")
        return problems
    seen = []
    for i, version in enumerate(versions):
        if not isinstance(version, dict):
            problems.append(f"version {i} is not an object")
            continue
        name = version.get("version")
        label = code(name) if isinstance(name, str) else f"version {i}"
        if not isinstance(name, str) or not VERSION.fullmatch(name):
            problems.append(f"{label}: `version` must be three numbers, such as `1.0.0`")
        elif name in seen:
            problems.append(f"{label} is listed twice")
        else:
            seen.append(name)
        problems += [f"{label}: {p}" for p in url_problems(version, repo)]
    # The website shows only the first version
    newest = max(seen, key=version_key, default=None)
    if seen and seen[0] != newest:
        problems.append(f"put the newest version, {code(newest)}, first in `versions`")
    return problems


def check_theme(theme, previous, github, author, report):
    """Checks one theme that the pull request added or changed."""
    theme_id = theme.get("id")
    problems = theme_problems(theme)
    if problems:
        report.problems += [f"{code(theme_id)}: {p}" for p in problems]
        return
    owner = theme["repo"].split("/")[0]
    old_versions = {v["version"]: v for v in previous["versions"]} if previous else {}
    names = [v["version"] for v in theme["versions"]]
    if previous is not None and previous.get("repo") != theme["repo"]:
        report.notes.append(
            f"{code(theme_id)} moves from {code(previous.get('repo'))} to {code(theme['repo'])}."
        )
    if author is not None and author.lower() != owner.lower():
        report.notes.append(
            f"{code(author)} opened this pull request, but {code(theme['repo'])} is under "
            f"{code(owner)}. Check that the owner agreed."
        )
    for name in old_versions:
        if name not in names:
            report.notes.append(f"Removes {code(theme_id)} {code(name)}.")
    for version in theme["versions"]:
        label = f"{code(theme_id)} {code(version['version'])}"
        old = old_versions.get(version["version"])
        if old is not None:
            for key in ("url", "sha256"):
                if old.get(key) != version.get(key):
                    report.problems.append(f"{label} {already_listed(key)}")
            continue
        try:
            data = check_release(version, github, MAX_THEME_ZIP_BYTES)
            ignored = read_theme_zip(data, theme_id, version["version"], github.public_tokens())
        # read_file reports a file over its limit as a ThemeError
        except (Problem, ThemeError, OSError) as e:
            report.problems.append(f"{label}: {e}")
            continue
        if ignored:
            report.notes.append(
                f"{label}: these variables in `tokens` are not public, so they do nothing: "
                f"{', '.join(code(t) for t in ignored)}."
            )
        report.notes.append(f"Import {label} into Hindsight and look at it.")


def read_theme_zip(data, theme_id, version, public_tokens):
    """Checks a theme zip as Hindsight imports it. Returns the tokens that are not public."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            theme_json = read_file(z, f"{theme_id}/theme.json", MAX_JSON_BYTES)
            css = read_file(z, f"{theme_id}/theme.css", MAX_CSS_BYTES)
    except (zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError) as e:
        raise Problem(f"the zip cannot be read: {e}") from e
    if theme_json is None:
        raise Problem(f"the zip has no {theme_id}/theme.json")
    try:
        file = json.loads(theme_json.decode("utf-8"))
    except ValueError as e:
        raise Problem(f"theme.json is not valid JSON: {e}") from e
    ignored = check_theme_manifest(file, theme_id, version, public_tokens)
    if css is not None:
        try:
            css_problems = theme_css_problems(css.decode("utf-8"))
        except UnicodeDecodeError as e:
            raise Problem("theme.css is not UTF-8") from e
        if css_problems:
            raise Problem(f"theme.css: {'; '.join(css_problems)}")
    return ignored


def check_theme_manifest(file, theme_id, version, public_tokens):
    """Checks theme.json with the rules of Hindsight. Returns the tokens that are not public."""
    if not isinstance(file, dict):
        raise Problem("theme.json is not a JSON object")
    if type(file.get("format")) is not int or file["format"] != 1:
        raise Problem("theme.json: `format` must be 1")
    if file.get("id") != theme_id:
        raise Problem(f"theme.json must have the id {code(theme_id)}")
    if file.get("version") != version:
        raise Problem(f"theme.json must have the version {code(version)}")
    name = file.get("name")
    if not isinstance(name, str) or not name.strip():
        raise Problem("theme.json: `name` must be a text that is not empty")
    author = file.get("author", "")
    if not isinstance(author, str):
        raise Problem("theme.json: `author` must be a text")
    for key, text in (("name", name), ("author", author)):
        if len(text) > MAX_TEXT_CHARS:
            raise Problem(f"theme.json: `{key}` is longer than {MAX_TEXT_CHARS} characters")
    for key in ("description", "tokens"):
        if not is_text_map(file.get(key, {})):
            raise Problem(f"theme.json: `{key}` must map names to texts")
    if file.get("layout", "card") not in ("card", "flat"):
        raise Problem("theme.json: `layout` must be card or flat")
    if file.get("mode", "light") not in ("light", "dark"):
        raise Problem("theme.json: `mode` must be light or dark")
    ignored = []
    for token, value in sorted(file.get("tokens", {}).items()):
        if token not in public_tokens:
            ignored.append(token)
        elif (
            not value.strip()
            or len(value) > MAX_TOKEN_VALUE_CHARS
            or any(c in ";{}" or unicodedata.category(c) == "Cc" for c in value)
        ):
            raise Problem(
                f"theme.json: {code(token)} must be 1 to {MAX_TOKEN_VALUE_CHARS} characters, "
                "without ;, {, } or control characters"
            )
    return ignored


def theme_css_problems(css):
    """Returns the places where theme.css loads something. Only data: addresses are allowed.

    Escapes are read first, so that `u\\72l(` is also found. Comments are not skipped, so an address
    in a comment is also reported.
    """
    css = CSS_ESCAPE.sub(unescape, css)
    problems = []
    if "@import" in css.lower():
        problems.append("`@import` is not allowed")
    for m in CSS_ADDRESS.finditer(css):
        if css[m.end() : m.end() + 5].lower() != "data:":
            problems.append(f"{code(m.group(0) + css[m.end() : m.end() + 40])} loads a file")
    for m in CSS_STRING_ADDRESS.finditer(css):
        for s in CSS_STRING.finditer(css[m.end() : find_closing(css, m.end())]):
            text = s.group(1) if s.group(1) is not None else s.group(2)
            if not text.lower().startswith("data:"):
                problems.append(f"{code(m.group(0) + s.group(0))} loads a file")
    return problems


def unescape(match):
    """Turns one CSS escape into the character it stands for."""
    if match.group(1) is None:
        return match.group(2)
    # The browser reads a number that is not a character as U+FFFD
    number = int(match.group(1), 16)
    return chr(number) if 0 < number < 0x110000 else "�"


def find_closing(css, start):
    """Returns the index of the ) that closes the ( just before start, or the end of css."""
    depth = 1
    for i in range(start, len(css)):
        if css[i] == "(":
            depth += 1
        elif css[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return len(css)


class GitHub:
    """Reads GitHub. Each repository and the schema are read at most once."""

    def __init__(self, token):
        self.token = token
        self.assets = {}
        self.tokens = None

    def fetch_assets(self, repo):
        if repo not in self.assets:
            self.assets[repo] = fetch_with_retries(lambda r: fetch_assets(r, self.token), repo)
        return self.assets[repo]

    def download(self, url, limit):
        def read(url):
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read(limit + 1)

        return fetch_with_retries(read, url)

    def public_tokens(self):
        if self.tokens is None:
            self.tokens = fetch_with_retries(fetch_public_tokens, SCHEMA_URL)
        return self.tokens


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def read_tree(revision):
    """Returns {path: contents} of the files at the revision.

    Only the files of the list are read. Another file maps to its git object id, which is enough to
    see whether it changed.
    """
    tree = {}
    for line in git("ls-tree", "-r", "-z", revision).split(b"\0"):
        if not line:
            continue
        meta, path = line.split(b"\t", 1)
        path = path.decode()
        object_id = meta.split()[2].decode()
        if path in LIST_FILES or path.startswith(ICONS):
            tree[path] = git("cat-file", "blob", object_id)
        else:
            tree[path] = object_id
    return tree


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("base")
    parser.add_argument("head")
    parser.add_argument("--author")
    args = parser.parse_args()
    merge_base = git("merge-base", args.base, args.head).decode().strip()
    report = check(
        read_tree(merge_base),
        read_tree(args.head),
        GitHub(os.environ.get("GITHUB_TOKEN")),
        args.author,
    )
    print(report.markdown())
    sys.exit(1 if report.problems else 0)


if __name__ == "__main__":
    main()
