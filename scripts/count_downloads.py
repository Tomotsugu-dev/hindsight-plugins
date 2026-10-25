"""Counts the downloads of each plugin in plugins.json and writes them to downloads.json.

The downloads of a plugin are the sum of the downloads of the zips that its versions point to.
Other files in the releases do not count.

Usage: python3 count_downloads.py <plugins.json> <downloads.json>
If the environment variable GITHUB_TOKEN is set, the GitHub API requests use it.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import unquote, urlparse

PLUGINS_JSON_FORMAT_VERSION = 2
DOWNLOADS_JSON_FORMAT_VERSION = 1

# Seconds to wait before the second and the third request
RETRY_DELAYS = (5, 30)
# The longest wait that Retry-After can ask for. The job runs once a day, so one plugin is not
# worth a longer wait
MAX_RETRY_AFTER = 60


def parse_url(url):
    """Splits the download URL of a release file into (repository, tag, file name).

    Returns None for other URLs. The URL looks like
    https://github.com/<owner>/<repo>/releases/download/<tag>/<file>.
    The repository is in lower case, because GitHub account and repository names ignore case.
    """
    parsed = urlparse(url)
    # The path starts with /, so the first part is an empty string
    parts = parsed.path.split("/")
    if (
        parsed.scheme != "https"
        or parsed.netloc != "github.com"
        or len(parts) != 7
        or parts[3:5] != ["releases", "download"]
    ):
        return None
    return f"{parts[1]}/{parts[2]}".lower(), unquote(parts[5]), unquote(parts[6])


def fetch_releases(repo, token):
    """Returns the downloads of each file in the latest 100 releases of the repository.

    The result maps (tag, file name) to the number of downloads.
    """
    return {key: asset["downloads"] for key, asset in fetch_assets(repo, token).items()}


def fetch_assets(repo, token):
    """Returns the downloads and digest of each file in the latest 100 releases of the repository.

    The result maps (tag, file name) to {"downloads": downloads, "digest": "sha256:…"}. If GitHub
    gives no digest for a file, its digest is None.
    """
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases?per_page=100",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        releases = json.load(response)
    return {
        (release["tag_name"], asset["name"]): {
            "downloads": asset["download_count"],
            "digest": asset.get("digest"),
        }
        for release in releases
        for asset in release["assets"]
    }


def fetch_with_retries(fetch, repo, sleep=time.sleep):
    """Calls fetch(repo). After a temporary error, waits and tries again, at most 3 times in all.

    Raises the error if it is not temporary, or if the third try also fails.
    """
    for delay in RETRY_DELAYS:
        try:
            return fetch(repo)
        except OSError as e:
            if not is_temporary(e):
                raise
            sleep(retry_after(e) or delay)
    return fetch(repo)


def is_temporary(error):
    """Returns whether sending the request again may succeed.

    True for no connection, timeouts, 5xx and rate limits. False for other HTTP errors.
    """
    if not isinstance(error, urllib.error.HTTPError):
        return True
    if error.code == 403:
        # GitHub may also return 403 for a rate limit. Then it sends Retry-After, or no requests
        # remain
        headers = error.headers or {}
        return "Retry-After" in headers or headers.get("X-RateLimit-Remaining") == "0"
    return error.code == 429 or error.code >= 500


def retry_after(error):
    """Returns the seconds that GitHub asks to wait, at most MAX_RETRY_AFTER.

    Returns None if GitHub does not ask.
    """
    headers = getattr(error, "headers", None) or {}
    value = headers.get("Retry-After")
    if value is None or not value.isdigit():
        return None
    return min(int(value), MAX_RETRY_AFTER)


def count(plugins, fetch):
    """Adds up the downloads of each plugin. Returns ({id: downloads}, [warnings]).

    fetch(repo) returns a dict like the one from fetch_releases. It is called once per repository.
    A plugin whose repository cannot be read is left out of the result. A version whose zip is not
    in the releases counts as 0.
    """
    releases = {}
    downloads = {}
    warnings = []
    for plugin in plugins:
        total = 0
        try:
            for version in plugin["versions"]:
                parsed = parse_url(version["url"])
                if parsed is None:
                    warnings.append(
                        f"{plugin['id']} {version['version']}: the url is not a release file"
                    )
                    continue
                repo, tag, name = parsed
                if repo not in releases:
                    releases[repo] = fetch(repo)
                n = releases[repo].get((tag, name))
                if n is None:
                    warnings.append(
                        f"{plugin['id']} {version['version']}: {name} is not in the latest "
                        f"100 releases of {repo}"
                    )
                    continue
                total += n
        # Network and HTTP errors are OSError, JSON errors are ValueError, and missing fields in the
        # response are KeyError
        except (OSError, ValueError, KeyError) as e:
            warnings.append(f"{plugin['id']}: {e}")
            continue
        downloads[plugin["id"]] = total
    return downloads, warnings


def main():
    source, target = sys.argv[1], sys.argv[2]
    with open(source, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("format_version") != PLUGINS_JSON_FORMAT_VERSION:
        sys.exit(f"plugins.json format version {data.get('format_version')} is not supported")
    plugins = data["plugins"]

    token = os.environ.get("GITHUB_TOKEN")

    def fetch(repo):
        return fetch_releases(repo, token)

    downloads, warnings = count(plugins, lambda repo: fetch_with_retries(fetch, repo))
    for warning in warnings:
        # GitHub Actions shows a line that starts with ::warning:: as a warning
        print(f"::warning::{warning}")
    # If no plugin could be counted, the network or the token most likely failed. Empty counts must
    # not replace the counts of the day before
    if plugins and not downloads:
        sys.exit("no plugin could be counted, so downloads.json is not written")

    with open(target, "w", encoding="utf-8") as f:
        json.dump(
            {
                "format_version": DOWNLOADS_JSON_FORMAT_VERSION,
                "downloads": dict(sorted(downloads.items())),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")


if __name__ == "__main__":
    main()
