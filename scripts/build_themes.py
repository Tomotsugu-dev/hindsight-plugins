"""Builds the files of the theme website from themes.json: index.json, and <id>.json for each theme.

Only the first version in versions of each theme is used. The digest of the zip in the release must
be the sha256 in themes.json, and the zip is checked again when it is first downloaded. If the last
run already built the same sha256, its result is used and the zip is not downloaded again, so that
the downloads are not counted too many times.

Usage: python3 build_themes.py <themes.json> <output folder>
If the environment variable GITHUB_TOKEN is set, the GitHub API requests use it.
"""

import hashlib
import io
import json
import os
import re
import sys
import urllib.request
import zipfile
import zlib
from urllib.parse import quote, urlparse

from count_downloads import count, fetch_assets, fetch_with_retries, parse_url

THEMES_JSON_FORMAT_VERSION = 1
INDEX_JSON_FORMAT_VERSION = 1

# The format of theme.json that Hindsight reads
THEME_FORMAT = 1

# The same limits as when Hindsight reads theme files
MAX_JSON_BYTES = 64 * 1024
MAX_CSS_BYTES = 512 * 1024
# The zip can also have other files, such as a README
MAX_ZIP_BYTES = 5 * 1024 * 1024

# The names of the public variables are read from here. A Hindsight test makes sure that this file
# matches PUBLIC_TOKENS in Hindsight
SCHEMA_URL = (
    "https://raw.githubusercontent.com/Tomotsugu-dev/Hindsight/main/"
    "docs/design/themes/theme.schema.json"
)

# The same rule as for theme ids in Hindsight: lowercase letters, digits and -, 1 to 63 characters,
# and not starting or ending with -
ID = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")

INDEX = "index.json"

# The fields of a record in index.json that come from theme.json
THEME_FIELDS = ("name", "author", "description", "version", "layout", "mode", "tokens")


class ThemeError(Exception):
    """The theme cannot be shown. The message goes into the warnings."""


def build(themes, fetch_assets, download, previous, public_tokens):
    """Builds the record in index.json and the preview of each theme.

    Returns (entries, previews, warnings).

    themes is themes in themes.json. fetch_assets(repo) returns
    {(tag, file name): {"downloads": downloads, "digest": "sha256:…"}}, and is called once per
    repository. download(url) returns the contents of the zip. previous is the result of the last
    run, {id: (entry, preview)}, or {} on the first run. public_tokens is the set of public variable
    names.

    Each record in entries has id, name, author, description, version, layout, mode, tokens, repo,
    homepage, release_url, sha256 and downloads. Records with more downloads come first, and records
    with the same downloads keep the order of themes.json. previews is
    {id: {"id", "layout", "mode", "tokens", "css"}}. A theme that cannot be read is left out of the
    result, and the reason goes into warnings.
    """
    assets = {}

    def fetch(repo):
        if repo not in assets:
            assets[repo] = fetch_assets(repo)
        return assets[repo]

    warnings = []
    listed = []
    for theme in themes:
        if is_listed_theme(theme):
            listed.append(theme)
        else:
            theme_id = theme.get("id") if isinstance(theme, dict) else None
            warnings.append(
                f"{theme_id}: the entry in themes.json misses a field or has a wrong type"
            )

    downloads, count_warnings = count(
        listed, lambda repo: {key: asset["downloads"] for key, asset in fetch(repo).items()}
    )
    warnings += count_warnings

    entries = []
    previews = {}
    for theme in listed:
        # A theme whose repository cannot be read is not in downloads, and count already wrote a
        # warning
        if theme["id"] not in downloads:
            continue
        version = theme["versions"][0]
        try:
            entry, preview = build_theme(
                theme, version, fetch, download, previous.get(theme["id"]), public_tokens
            )
        except (ThemeError, OSError) as e:
            warnings.append(f"{theme['id']} {version['version']}: {e}")
            continue
        entry["downloads"] = downloads[theme["id"]]
        entries.append(entry)
        previews[theme["id"]] = preview
    # sort is stable, also with reverse: themes with the same downloads keep their order
    entries.sort(key=lambda entry: entry["downloads"], reverse=True)
    return entries, previews, warnings


def is_listed_theme(theme):
    """Returns whether this record of themes.json has the fields it needs, with the right types."""
    return (
        isinstance(theme, dict)
        and isinstance(theme.get("id"), str)
        and isinstance(theme.get("repo"), str)
        and ("homepage" not in theme or isinstance(theme["homepage"], str))
        and isinstance(theme.get("versions"), list)
        and len(theme["versions"]) > 0
        and all(
            isinstance(version, dict)
            and all(isinstance(version.get(key), str) for key in ("version", "url", "sha256"))
            for version in theme["versions"]
        )
    )


def build_theme(theme, version, fetch, download, previous, public_tokens):
    """Builds the record of one theme in index.json, without downloads yet, and its preview."""
    theme_id = theme["id"]
    # The id is used as a file name, and index would have the same name as index.json
    if not ID.fullmatch(theme_id) or f"{theme_id}.json" == INDEX:
        raise ThemeError("the id cannot be used as a file name")
    homepage = theme.get("homepage", f"https://github.com/{theme['repo']}")
    # The website puts it in a link. Only https is allowed: a link to an address such as
    # javascript: runs on the website when it is clicked
    parsed_homepage = urlparse(homepage)
    if parsed_homepage.scheme != "https" or not parsed_homepage.netloc:
        raise ThemeError(f"the homepage {homepage!r} is not an https address")
    parsed = parse_url(version["url"])
    if parsed is None:
        raise ThemeError("the url is not a file in a GitHub release")
    repo, tag, name = parsed
    if repo != theme["repo"].lower():
        raise ThemeError(f"the url is not in {theme['repo']}")
    sha256 = version["sha256"].lower()
    asset = fetch(repo).get((tag, name))
    if asset is None:
        raise ThemeError(f"{name} is not in the latest 100 releases of {repo}")
    if asset["digest"] != f"sha256:{sha256}":
        raise ThemeError(f"{name} in the release is not the zip whose sha256 is in themes.json")

    if previous is not None and previous[0]["sha256"] == sha256:
        old_entry, preview = previous
        fields = {key: old_entry[key] for key in THEME_FIELDS}
    else:
        data = download(version["url"])
        if hashlib.sha256(data).hexdigest() != sha256:
            raise ThemeError("the downloaded zip does not match the sha256 in themes.json")
        fields, css = read_theme(data, theme_id, version["version"], public_tokens)
        preview = {
            "id": theme_id,
            "layout": fields["layout"],
            "mode": fields["mode"],
            "tokens": fields["tokens"],
            "css": css,
        }
    entry = {
        "id": theme_id,
        **fields,
        "repo": theme["repo"],
        "homepage": homepage,
        "release_url": f"https://github.com/{theme['repo']}/releases/tag/{quote(tag, safe='')}",
        "sha256": sha256,
    }
    return entry, preview


def read_theme(data, theme_id, version, public_tokens):
    """Reads and checks <id>/theme.json and <id>/theme.css in the zip. Returns (fields, css).

    fields has the fields in THEME_FIELDS. Without theme.css, css is None.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            theme_json = read_file(z, f"{theme_id}/theme.json", MAX_JSON_BYTES)
            css = read_file(z, f"{theme_id}/theme.css", MAX_CSS_BYTES)
    # Not a zip, broken contents, a compression method that is not supported, or a password
    except (zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError) as e:
        raise ThemeError(f"the zip cannot be read: {e}") from e
    if theme_json is None:
        raise ThemeError(f"the zip has no {theme_id}/theme.json")
    try:
        file = json.loads(theme_json.decode("utf-8"))
    except ValueError as e:
        raise ThemeError(f"theme.json cannot be read: {e}") from e
    if css is not None:
        try:
            css = css.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ThemeError("theme.css is not UTF-8") from e
    return check_theme_json(file, theme_id, version, public_tokens), css


def read_file(z, path, limit):
    """Reads one file in the zip, at most limit bytes. Returns None if the zip does not have it."""
    try:
        info = z.getinfo(path)
    except KeyError:
        return None
    # Reading 1 more byte shows whether the file is over the limit. The size written in the zip can
    # be false, so it is not enough to check it
    with z.open(info) as f:
        content = f.read(limit + 1)
    if len(content) > limit:
        raise ThemeError(f"{path} is larger than {limit // 1024} KB")
    return content


def check_theme_json(file, theme_id, version, public_tokens):
    """Checks theme.json and returns the fields in THEME_FIELDS. tokens keeps only public variables.

    Only what the website needs is checked. The full check is at PR review: import the theme into
    Hindsight once.
    """
    if not isinstance(file, dict):
        raise ThemeError("theme.json is not a JSON object")
    if file.get("format") != THEME_FORMAT:
        raise ThemeError(f"theme.json format {file.get('format')} is not supported")
    if file.get("id") != theme_id:
        raise ThemeError(f"theme.json has the id {file.get('id')!r}, not {theme_id!r}")
    if file.get("version") != version:
        raise ThemeError(f"theme.json has the version {file.get('version')!r}, not {version!r}")
    name = file.get("name")
    author = file.get("author", "")
    description = file.get("description", {})
    layout = file.get("layout", "card")
    mode = file.get("mode", "light")
    tokens = file.get("tokens", {})
    if not isinstance(name, str) or not name.strip():
        raise ThemeError("theme.json has no name")
    if not isinstance(author, str):
        raise ThemeError("author is not a string")
    if not is_string_map(description):
        raise ThemeError("description is not a map from language code to text")
    if layout not in ("card", "flat"):
        raise ThemeError(f"layout {layout!r} is not card or flat")
    if mode not in ("light", "dark"):
        raise ThemeError(f"mode {mode!r} is not light or dark")
    if not is_string_map(tokens):
        raise ThemeError("tokens is not a map from variable name to value")
    return {
        "name": name,
        "author": author,
        "description": description,
        "version": version,
        "layout": layout,
        "mode": mode,
        "tokens": {key: value for key, value in tokens.items() if key in public_tokens},
    }


def is_string_map(value):
    return isinstance(value, dict) and all(isinstance(v, str) for v in value.values())


def run(themes, fetch_assets, download, public_tokens, folder):
    """Builds the theme files and writes them into folder. Returns (whether it wrote, warnings).

    The result of the last run is read from folder. The <id>.json of a theme that was not built is
    removed. If no repository can be read (most likely the network or the token failed), nothing is
    written, and the last result stays.
    """
    fetched = []

    def fetch(repo):
        result = fetch_assets(repo)
        fetched.append(repo)
        return result

    entries, previews, warnings = build(
        themes, fetch, download, read_previous(folder), public_tokens
    )
    if themes and not fetched:
        return False, warnings

    os.makedirs(folder, exist_ok=True)
    index = {"format_version": INDEX_JSON_FORMAT_VERSION, "themes": entries}
    write_json(os.path.join(folder, INDEX), index)
    for theme_id, preview in previews.items():
        write_json(os.path.join(folder, f"{theme_id}.json"), preview)
    for name in os.listdir(folder):
        if name != INDEX and name.removesuffix(".json") not in previews:
            os.remove(os.path.join(folder, name))
    return True, warnings


def read_previous(folder):
    """Reads what the last run wrote. Returns {id: (entry, preview)}.

    A part that cannot be read is treated as missing: at worst, the zip is downloaded once more.
    """
    try:
        with open(os.path.join(folder, INDEX), encoding="utf-8") as f:
            index = json.load(f)
    except (OSError, ValueError):
        return {}
    if (
        not isinstance(index, dict)
        or index.get("format_version") != INDEX_JSON_FORMAT_VERSION
        or not isinstance(index.get("themes"), list)
    ):
        return {}
    previous = {}
    for entry in index["themes"]:
        if not (
            isinstance(entry, dict)
            and isinstance(entry.get("id"), str)
            and ID.fullmatch(entry["id"])
            and all(key in entry for key in THEME_FIELDS + ("sha256",))
        ):
            continue
        try:
            with open(os.path.join(folder, f"{entry['id']}.json"), encoding="utf-8") as f:
                previous[entry["id"]] = (entry, json.load(f))
        except (OSError, ValueError):
            continue
    return previous


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def fetch_public_tokens(url):
    """Reads the names of the public variables from theme.schema.json of Hindsight."""
    with urllib.request.urlopen(url, timeout=30) as response:
        schema = json.load(response)
    return set(schema["properties"]["tokens"]["properties"])


def download_zip(url):
    """Downloads the zip in the release, at most MAX_ZIP_BYTES."""
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(MAX_ZIP_BYTES + 1)
    if len(data) > MAX_ZIP_BYTES:
        raise ThemeError(f"the zip is larger than {MAX_ZIP_BYTES // 1024 // 1024} MB")
    return data


def main():
    source, folder = sys.argv[1], sys.argv[2]
    with open(source, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("format_version") != THEMES_JSON_FORMAT_VERSION:
        sys.exit(f"themes.json format version {data.get('format_version')} is not supported")
    themes = data["themes"]

    token = os.environ.get("GITHUB_TOKEN")
    public_tokens = fetch_with_retries(fetch_public_tokens, SCHEMA_URL)
    wrote, warnings = run(
        themes,
        lambda repo: fetch_with_retries(lambda r: fetch_assets(r, token), repo),
        lambda url: fetch_with_retries(download_zip, url),
        public_tokens,
        folder,
    )
    for warning in warnings:
        # GitHub Actions shows a line that starts with ::warning:: as a warning
        print(f"::warning::{warning}")
    if not wrote:
        sys.exit("no repository could be read, so the theme files are not written")


if __name__ == "__main__":
    main()
