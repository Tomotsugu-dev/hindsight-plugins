"""build_themes.py 的测试。不联网：GitHub 用 FakeGitHub 代替。

运行：cd scripts && python3 -m unittest test_build_themes
"""

import hashlib
import io
import json
import os
import tempfile
import unittest
import zipfile

from build_themes import MAX_CSS_BYTES, MAX_JSON_BYTES, build, run

PUBLIC_TOKENS = {"--color-accent", "--surface-app"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def theme_json(theme_id="harbor", version="1.0.0", **fields):
    """一个合规的 theme.json；fields 里的字段覆盖默认值。"""
    data = {
        "format": 1,
        "id": theme_id,
        "name": "Harbor",
        "version": version,
        "author": "someone",
        "description": {"en": "Slate blue on cool grey."},
        "layout": "card",
        "mode": "light",
        "tokens": {"--color-accent": "#3b6e8f"},
    }
    data.update(fields)
    return data


def make_zip(files):
    """files 是 {zip 里的路径: 内容}。内容是 dict 时写成 JSON。"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for path, content in files.items():
            if isinstance(content, dict):
                content = json.dumps(content)
            z.writestr(path, content)
    return buffer.getvalue()


def theme_zip(theme_id="harbor", version="1.0.0", css="[data-part='card'] { border: 0; }", **fields):
    files = {f"{theme_id}/theme.json": theme_json(theme_id, version, **fields)}
    if css is not None:
        files[f"{theme_id}/theme.css"] = css
    return make_zip(files)


class FakeGitHub:
    """假的 GitHub：记下每个 release 文件的内容、下载次数和 digest。"""

    def __init__(self):
        self.files = {}
        self.downloads = {}
        self.digests = {}
        self.downloaded = []
        self.broken_repos = set()

    def publish(self, repo, tag, data, downloads=0):
        """在 repo 的 release tag 里上传一个 zip，返回它的下载地址。"""
        name = f"{repo.split('/')[1]}-{tag}.zip"
        url = f"https://github.com/{repo}/releases/download/{tag}/{name}"
        self.files[url] = data
        self.downloads[url] = downloads
        self.digests[url] = f"sha256:{sha256(data)}"
        return url

    def replace(self, url, data):
        """作者删掉 release 里的 zip，再传一个同名的。"""
        self.files[url] = data
        self.digests[url] = f"sha256:{sha256(data)}"

    def fetch_assets(self, repo):
        if repo in self.broken_repos:
            raise OSError(f"cannot read {repo}")
        result = {}
        for url in self.files:
            parts = url.split("/")
            if f"{parts[3]}/{parts[4]}".lower() == repo:
                result[(parts[7], parts[8])] = {
                    "downloads": self.downloads[url],
                    "digest": self.digests[url],
                }
        return result

    def download(self, url):
        self.downloaded.append(url)
        return self.files[url]

    def build(self, themes, previous=None):
        return build(themes, self.fetch_assets, self.download, previous or {}, PUBLIC_TOKENS)


def listed(theme_id, repo, *versions):
    """themes.json 里的一条。versions 是 (版本号, 地址, zip 内容)，新版本在前。"""
    return {
        "id": theme_id,
        "repo": repo,
        "versions": [
            {"version": version, "url": url, "sha256": sha256(data)}
            for version, url, data in versions
        ],
    }


def one_theme(github, theme_id="harbor", repo="someone/hindsight-harbor", downloads=0, **zip_fields):
    """上传一个主题的 1.0.0，返回它在 themes.json 里的一条。"""
    data = theme_zip(theme_id, **zip_fields)
    url = github.publish(repo, "1.0.0", data, downloads)
    return listed(theme_id, repo, ("1.0.0", url, data))


class BuildTest(unittest.TestCase):
    # 作者换了 release 里的 zip：digest 和 themes.json 的 sha256 对不上，这个主题不显示，也不去下载
    def test_skips_a_theme_whose_digest_differs(self):
        github = FakeGitHub()
        harbor = one_theme(github)
        github.replace(harbor["versions"][0]["url"], theme_zip(css="body { display: none; }"))

        entries, previews, warnings = github.build([harbor])

        self.assertEqual(entries, [])
        self.assertEqual(previews, {})
        self.assertEqual(github.downloaded, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("harbor", warnings[0])

    # digest 对得上，下载到的内容却不一样：第一次下载也要核对 sha256
    def test_skips_a_zip_whose_sha256_differs(self):
        github = FakeGitHub()
        harbor = one_theme(github)
        github.files[harbor["versions"][0]["url"]] = theme_zip(css="body { display: none; }")

        entries, _, warnings = github.build([harbor])

        self.assertEqual(entries, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("harbor", warnings[0])

    # 只收 GitHub release 里的文件：别的地址跳过，其余主题照常
    def test_skips_a_url_that_is_not_a_github_release(self):
        github = FakeGitHub()
        data = theme_zip("nord")
        nord = listed("nord", "someone/nord", ("1.0.0", "https://example.com/nord-1.0.0.zip", data))
        harbor = one_theme(github)

        entries, _, warnings = github.build([nord, harbor])

        self.assertEqual([e["id"] for e in entries], ["harbor"])
        self.assertTrue(any("nord" in w for w in warnings))

    # 地址不在 themes.json 写的仓库里：卡片上的仓库和下载的地方要是同一个
    def test_skips_a_url_outside_the_listed_repo(self):
        github = FakeGitHub()
        data = theme_zip()
        url = github.publish("other/hindsight-harbor", "1.0.0", data)
        harbor = listed("harbor", "someone/hindsight-harbor", ("1.0.0", url, data))

        entries, _, warnings = github.build([harbor])

        self.assertEqual(entries, [])
        self.assertEqual(len(warnings), 1)

    # 文件要在 zip 里用 id 命名的文件夹里：直接放在 zip 根上的不认
    def test_reads_files_from_the_id_folder(self):
        github = FakeGitHub()
        flat = make_zip({"theme.json": theme_json("nord"), "theme.css": "a {}"})
        url = github.publish("someone/nord", "1.0.0", flat)
        nord = listed("nord", "someone/nord", ("1.0.0", url, flat))
        harbor = one_theme(github, css="[data-part='card'] { border: 0; }")

        entries, previews, warnings = github.build([nord, harbor])

        self.assertEqual([e["id"] for e in entries], ["harbor"])
        self.assertEqual(previews["harbor"]["css"], "[data-part='card'] { border: 0; }")
        self.assertEqual(len(warnings), 1)
        self.assertIn("nord", warnings[0])

    # 上一次已经生成过同一个 sha256：不再下载，免得下载次数多算；下载次数还是用最新的
    def test_does_not_download_a_version_it_already_built(self):
        github = FakeGitHub()
        harbor = one_theme(github, downloads=3)
        entries, previews, _ = github.build([harbor])
        previous = {"harbor": (entries[0], previews["harbor"])}
        github.downloaded.clear()
        github.downloads[harbor["versions"][0]["url"]] = 8

        again, again_previews, warnings = github.build([harbor], previous)

        self.assertEqual(github.downloaded, [])
        self.assertEqual(again[0]["downloads"], 8)
        self.assertEqual(again_previews, previews)
        self.assertEqual(warnings, [])

    # 一个主题的 zip 坏了、仓库读不到，只跳过它，其余主题照常
    def test_a_bad_theme_does_not_stop_the_others(self):
        github = FakeGitHub()
        url = github.publish("someone/broken", "1.0.0", b"not a zip")
        broken = listed("broken", "someone/broken", ("1.0.0", url, b"not a zip"))
        gone = one_theme(github, "gone", "someone/gone")
        github.broken_repos.add("someone/gone")
        harbor = one_theme(github)

        entries, _, warnings = github.build([broken, gone, harbor])

        self.assertEqual([e["id"] for e in entries], ["harbor"])
        self.assertTrue(any("broken" in w for w in warnings))
        self.assertTrue(any("gone" in w for w in warnings))

    # themes.json 里的一条少了字段、类型不对：跳过这一条，其余照常
    def test_skips_an_entry_without_the_fields_it_needs(self):
        github = FakeGitHub()
        harbor = one_theme(github)
        bad = [
            "harbor",
            {"id": "nord", "repo": "someone/nord", "versions": []},
            {"id": "nord", "repo": "someone/nord", "versions": [{"version": "1.0.0"}]},
            {"repo": "someone/nord", "versions": harbor["versions"]},
            dict(harbor, homepage=None),
        ]

        entries, _, warnings = github.build(bad + [harbor])

        self.assertEqual([e["id"] for e in entries], ["harbor"])
        self.assertEqual(len(warnings), len(bad))

    # theme.json 里的 id、版本号要和 themes.json 写的一样
    def test_skips_a_theme_whose_id_or_version_differs_from_the_list(self):
        for theme_id, version in [("other", "1.0.0"), ("harbor", "2.0.0")]:
            github = FakeGitHub()
            data = make_zip({"harbor/theme.json": theme_json(theme_id, version)})
            url = github.publish("someone/hindsight-harbor", "1.0.0", data)
            harbor = listed("harbor", "someone/hindsight-harbor", ("1.0.0", url, data))

            entries, _, warnings = github.build([harbor])

            self.assertEqual(entries, [], (theme_id, version))
            self.assertEqual(len(warnings), 1, (theme_id, version))

    # id 要当文件名用：不合规的、和 index.json 撞名的都不收
    def test_skips_an_id_that_cannot_be_a_file_name(self):
        for theme_id in ["../harbor", "Harbor", "index"]:
            github = FakeGitHub()
            data = theme_zip(theme_id)
            url = github.publish("someone/hindsight-harbor", "1.0.0", data)
            harbor = listed(theme_id, "someone/hindsight-harbor", ("1.0.0", url, data))

            entries, _, warnings = github.build([harbor])

            self.assertEqual(entries, [], theme_id)
            self.assertEqual(len(warnings), 1, theme_id)

    # theme.json 超过 64 KB、theme.css 超过 512 KB，和 Hindsight 一样不收
    def test_skips_files_over_their_size_limits(self):
        cases = [
            {"description": {"en": "x" * MAX_JSON_BYTES}},
            {"css": "a {}" + " " * MAX_CSS_BYTES},
        ]
        for fields in cases:
            github = FakeGitHub()
            harbor = one_theme(github, **fields)

            entries, _, warnings = github.build([harbor])

            self.assertEqual(entries, [], list(fields))
            self.assertEqual(len(warnings), 1, list(fields))

    # tokens 只留公开变量，和 Hindsight 套用主题时一样
    def test_keeps_only_public_tokens(self):
        github = FakeGitHub()
        harbor = one_theme(github, tokens={"--color-accent": "#3b6e8f", "--private": "red"})

        entries, previews, _ = github.build([harbor])

        self.assertEqual(entries[0]["tokens"], {"--color-accent": "#3b6e8f"})
        self.assertEqual(previews["harbor"]["tokens"], {"--color-accent": "#3b6e8f"})

    # 名称、作者、简介从 zip 里的 theme.json 读，themes.json 不写这些
    def test_takes_name_author_and_description_from_theme_json(self):
        github = FakeGitHub()
        harbor = one_theme(github, name="港湾", author="Yoshino", description={"zh-CN": "冷灰底色"})

        entries, previews, _ = github.build([harbor])

        entry = entries[0]
        self.assertEqual(entry["name"], "港湾")
        self.assertEqual(entry["author"], "Yoshino")
        self.assertEqual(entry["description"], {"zh-CN": "冷灰底色"})
        self.assertEqual(entry["layout"], "card")
        self.assertEqual(entry["mode"], "light")
        self.assertEqual(entry["repo"], "someone/hindsight-harbor")
        self.assertEqual(entry["sha256"], harbor["versions"][0]["sha256"])
        self.assertEqual(
            previews["harbor"],
            {
                "id": "harbor",
                "layout": "card",
                "mode": "light",
                "tokens": {"--color-accent": "#3b6e8f"},
                "css": "[data-part='card'] { border: 0; }",
            },
        )

    # 没有 theme.css 时，预览的 css 是 None
    def test_a_theme_without_css(self):
        github = FakeGitHub()
        harbor = one_theme(github, css=None)

        _, previews, _ = github.build([harbor])

        self.assertIsNone(previews["harbor"]["css"])

    # 「下载」跳到这个版本的 Release 页面
    def test_points_download_to_the_release_page(self):
        github = FakeGitHub()
        harbor = one_theme(github)

        entries, _, _ = github.build([harbor])

        self.assertEqual(
            entries[0]["release_url"],
            "https://github.com/someone/hindsight-harbor/releases/tag/1.0.0",
        )

    # 「主页」用 themes.json 的 homepage；没写时用仓库的 GitHub 页面
    def test_uses_the_homepage_or_the_repo(self):
        github = FakeGitHub()
        harbor = one_theme(github)
        nord = dict(one_theme(github, "nord", "someone/nord"), homepage="https://nord.example/")

        entries, _, _ = github.build([harbor, nord])

        homepages = {e["id"]: e["homepage"] for e in entries}
        self.assertEqual(
            homepages,
            {"harbor": "https://github.com/someone/hindsight-harbor", "nord": "https://nord.example/"},
        )

    # homepage 会放进官网的链接里：不是 https 的不收
    def test_skips_a_homepage_that_is_not_https(self):
        for homepage in ["http://nord.example/", "javascript:alert(1)", "https://", "nord.example"]:
            github = FakeGitHub()
            nord = dict(one_theme(github, "nord", "someone/nord"), homepage=homepage)

            entries, _, warnings = github.build([nord])

            self.assertEqual(entries, [], homepage)
            self.assertEqual(len(warnings), 1, homepage)

    # 网站只显示第一个版本；下载次数是所有版本加起来
    def test_uses_the_first_version(self):
        github = FakeGitHub()
        repo = "someone/hindsight-harbor"
        new, old = theme_zip(version="1.1.0"), theme_zip(version="1.0.0")
        new_url = github.publish(repo, "1.1.0", new, downloads=2)
        old_url = github.publish(repo, "1.0.0", old, downloads=5)
        harbor = listed("harbor", repo, ("1.1.0", new_url, new), ("1.0.0", old_url, old))

        entries, _, _ = github.build([harbor])

        self.assertEqual(entries[0]["version"], "1.1.0")
        self.assertEqual(entries[0]["downloads"], 7)
        self.assertEqual(github.downloaded, [new_url])

    # 按下载次数从多到少排；一样多的保持 themes.json 的顺序
    def test_sorts_by_downloads_and_keeps_list_order_on_ties(self):
        github = FakeGitHub()
        themes = [
            one_theme(github, "alpha", "someone/alpha", downloads=5),
            one_theme(github, "beta", "someone/beta", downloads=9),
            one_theme(github, "gamma", "someone/gamma", downloads=5),
        ]

        entries, _, _ = github.build(themes)

        self.assertEqual([e["id"] for e in entries], ["beta", "alpha", "gamma"])


def read_folder(folder):
    """返回 {文件名: 读出来的 JSON}。"""
    result = {}
    for name in sorted(os.listdir(folder)):
        with open(os.path.join(folder, name), encoding="utf-8") as f:
            result[name] = json.load(f)
    return result


class RunTest(unittest.TestCase):
    # 写出 index.json 和每个主题的 <id>.json；下架的主题，它的文件被删掉。第二次跑从文件夹里读上一次的结果，不再下载
    def test_removes_files_of_themes_no_longer_listed(self):
        github = FakeGitHub()
        alpha = one_theme(github, "alpha", "someone/alpha")
        beta = one_theme(github, "beta", "someone/beta")
        with tempfile.TemporaryDirectory() as folder:
            wrote, _ = run([alpha, beta], github.fetch_assets, github.download, PUBLIC_TOKENS, folder)
            self.assertTrue(wrote)
            self.assertEqual(sorted(os.listdir(folder)), ["alpha.json", "beta.json", "index.json"])
            github.downloaded.clear()

            wrote, _ = run([alpha], github.fetch_assets, github.download, PUBLIC_TOKENS, folder)

            self.assertTrue(wrote)
            files = read_folder(folder)
            self.assertEqual(sorted(files), ["alpha.json", "index.json"])
            self.assertEqual(files["index.json"]["format_version"], 1)
            self.assertEqual([t["id"] for t in files["index.json"]["themes"]], ["alpha"])
            self.assertEqual(github.downloaded, [])

    # 一个仓库都读不到：多半是网络或 token 坏了，不能拿空结果盖掉上一次的
    def test_writes_nothing_when_no_theme_could_be_built(self):
        github = FakeGitHub()
        harbor = one_theme(github)
        with tempfile.TemporaryDirectory() as folder:
            run([harbor], github.fetch_assets, github.download, PUBLIC_TOKENS, folder)
            before = read_folder(folder)
            github.broken_repos.add("someone/hindsight-harbor")

            wrote, warnings = run([harbor], github.fetch_assets, github.download, PUBLIC_TOKENS, folder)

            self.assertFalse(wrote)
            self.assertEqual(len(warnings), 1)
            self.assertEqual(read_folder(folder), before)

    # 列表里只有一个主题，作者换了它的 zip：仓库读得到，照常写，这个主题从文件里删掉，
    # 不能留着上一次的预览
    def test_removes_a_theme_whose_zip_was_replaced(self):
        github = FakeGitHub()
        harbor = one_theme(github)
        with tempfile.TemporaryDirectory() as folder:
            run([harbor], github.fetch_assets, github.download, PUBLIC_TOKENS, folder)
            github.replace(harbor["versions"][0]["url"], theme_zip(css="body { display: none; }"))

            wrote, warnings = run([harbor], github.fetch_assets, github.download, PUBLIC_TOKENS, folder)

            self.assertTrue(wrote)
            self.assertEqual(len(warnings), 1)
            self.assertEqual(read_folder(folder), {"index.json": {"format_version": 1, "themes": []}})

    # 列表本来就是空的：照常写一个空的 index.json
    def test_writes_an_empty_index_for_an_empty_list(self):
        github = FakeGitHub()
        with tempfile.TemporaryDirectory() as folder:
            wrote, _ = run([], github.fetch_assets, github.download, PUBLIC_TOKENS, folder)

            self.assertTrue(wrote)
            self.assertEqual(read_folder(folder), {"index.json": {"format_version": 1, "themes": []}})


if __name__ == "__main__":
    unittest.main()
