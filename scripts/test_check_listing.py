"""check_listing.py 的测试。不联网：GitHub 用 FakeGitHub 代替。

运行：cd scripts && python3 -m unittest test_check_listing
"""

import io
import json
import unittest
import zipfile

import test_build_themes
from check_listing import check, theme_css_problems
from test_build_themes import make_zip, sha256, theme_zip

PNG = b"\x89PNG\r\n\x1a\n" + b"icon"


class FakeGitHub(test_build_themes.FakeGitHub):
    def download(self, url, limit):
        return super().download(url)

    def public_tokens(self):
        return test_build_themes.PUBLIC_TOKENS


def manifest(plugin_id="hindsight-garden", version="0.1.0", **fields):
    """一个合规的 manifest.json；fields 里的字段覆盖默认值。"""
    data = {
        "id": plugin_id,
        "name": "Garden",
        "version": version,
        "permissions": ["notifications"],
        "runs_in_background": False,
    }
    data.update(fields)
    return data


def plugin_zip(icon=PNG, extra=None, **fields):
    files = {"manifest.json": manifest(**fields), "index.html": "<p>garden</p>"}
    if icon is not None:
        files["icon.png"] = icon
    files.update(extra or {})
    return make_zip(files)


def version_entry(github, repo, version, data, **fields):
    """把 zip 传到 repo 的 release，返回 plugins.json 里的一个版本。"""
    url = github.publish(repo, version, data)
    entry = {"version": version, "url": url, "sha256": sha256(data),
             "permissions": ["notifications"]}
    entry.update(fields)
    return entry


def plugin_entry(*versions, plugin_id="hindsight-garden", repo="someone/hindsight-garden"):
    return {
        "id": plugin_id,
        "name": "Garden",
        "author": "someone",
        "description": {"en": "Grow a garden while you focus"},
        "repo": repo,
        "versions": list(versions),
    }


def files(plugins=(), themes=(), **others):
    """仓库里的文件：两个清单、一个 README，再加上 others（比如图标）。"""
    result = {
        "plugins.json": json.dumps({"format_version": 2, "plugins": list(plugins)}).encode(),
        "themes.json": json.dumps({"format_version": 1, "themes": list(themes)}).encode(),
        "README.md": "readme",
    }
    result.update(others)
    return result


class PluginTest(unittest.TestCase):
    def setUp(self):
        self.github = FakeGitHub()
        self.repo = "someone/hindsight-garden"

    def new_plugin(self, data=None, **fields):
        data = data if data is not None else plugin_zip()
        return plugin_entry(version_entry(self.github, self.repo, "0.1.0", data, **fields))

    # 合规的第三方插件：没有问题；提醒审核者读代码、装上试
    def test_passes_a_valid_new_plugin(self):
        garden = self.new_plugin()
        head = files([garden], **{"icons/hindsight-garden.png": PNG})

        report = check(files(), head, self.github, author="someone")

        self.assertEqual(report.problems, [])
        notes = "\n".join(report.notes)
        self.assertIn("third-party", notes)
        self.assertIn("https://github.com/someone/hindsight-garden/tree/0.1.0", notes)
        self.assertIn("Install", notes)

    # 条目本身不合规：不联网就报出来，也不去下载
    def test_reports_an_entry_that_breaks_the_rules(self):
        garden = self.new_plugin()
        garden["id"] = "Garden"
        garden["description"] = {"zh": "花园"}
        version = garden["versions"][0]
        version["sha256"] = "abc"
        version["url"] = version["url"].replace("someone/hindsight-garden", "other/repo")
        version["permissions"] = ["focus.app", "camera"]
        version["storage_mb"] = 0

        problems = "\n".join(check(files(), files([garden]), self.github).problems)

        for text in ("`id`", "`zh`", "must have `en`", "`sha256`", "release file of",
                     "`focus.app` needs `focus.changed`", "`camera`", "`storage_mb`"):
            self.assertIn(text, problems)
        self.assertEqual(self.github.downloaded, [])

    # 已上架的版本改了 sha256：报错，叫作者发新版本
    def test_reports_a_changed_listed_version(self):
        garden = self.new_plugin()
        changed = json.loads(json.dumps(garden))
        changed["versions"][0]["sha256"] = "0" * 64

        report = check(files([garden]), files([changed]), self.github)

        self.assertEqual(len(report.problems), 1)
        self.assertIn("already listed", report.problems[0])

    # zip 里的 manifest 和清单对不上：版本号、权限、名字
    def test_reports_a_manifest_that_differs(self):
        cases = [
            ({"version": "0.2.0"}, "version"),
            ({"permissions": ["island"]}, "`permissions`"),
            ({"storage_mb": 5}, "`storage_mb`"),
            ({"name": "时光花园"}, "`name`"),
        ]
        for fields, text in cases:
            with self.subTest(text):
                self.github = FakeGitHub()
                garden = self.new_plugin(plugin_zip(**fields))
                head = files([garden], **{"icons/hindsight-garden.png": PNG})
                problems = check(files(), head, self.github).problems
                self.assertEqual(len(problems), 1, problems)
                self.assertIn(text, problems[0])

    # release 里的 zip 被换过：digest 对不上，不下载
    def test_reports_a_release_that_differs(self):
        garden = self.new_plugin()
        self.github.replace(garden["versions"][0]["url"], plugin_zip(icon=None))

        problems = check(files(), files([garden]), self.github).problems

        self.assertEqual(len(problems), 1)
        self.assertIn("does not match `sha256`", problems[0])
        self.assertEqual(self.github.downloaded, [])

    # Hindsight 装不上的包：跳出文件夹的路径、符号链接、后台运行却没有 background.js、图标不是 PNG
    def test_reports_a_zip_that_hindsight_rejects(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            z.writestr("manifest.json", json.dumps(manifest()))
            link = zipfile.ZipInfo("link")
            link.external_attr = 0o120777 << 16
            z.writestr(link, "../../hindsight.db")
        cases = [
            (buffer.getvalue(), "symlink"),
            (plugin_zip(extra={"../evil.js": "x"}), "unsafe path"),
            (plugin_zip(extra={"a\\..\\..\\evil.js": "x"}), "unsafe path"),
            (plugin_zip(runs_in_background=True), "background.js"),
            (plugin_zip(icon=b"GIF89a"), "not a PNG"),
        ]
        for data, text in cases:
            with self.subTest(text):
                self.github = FakeGitHub()
                garden = self.new_plugin(data)
                problems = check(files(), files([garden]), self.github).problems
                self.assertEqual(len(problems), 1, problems)
                self.assertIn(text, problems[0])

    # icons/<id>.png 和 zip 里的 icon.png 不是同一个文件，或者少了一个
    def test_reports_an_icon_that_differs(self):
        cases = [
            ({"icons/hindsight-garden.png": PNG + b"!"}, PNG, "same file"),
            ({}, PNG, "add"),
            ({"icons/hindsight-garden.png": PNG}, None, "remove"),
        ]
        for icons, in_zip, text in cases:
            with self.subTest(text):
                self.github = FakeGitHub()
                garden = self.new_plugin(plugin_zip(icon=in_zip))
                problems = check(files(), files([garden], **icons), self.github).problems
                self.assertEqual(len(problems), 1, problems)
                self.assertIn(text, problems[0])

    # 新版本：只下载新的那个；提醒新增的权限、更大的容量，给出代码对比的链接
    def test_notes_what_a_new_version_adds(self):
        old = version_entry(self.github, self.repo, "0.1.0", plugin_zip(), storage_mb=1)
        permissions = ["notifications", "island"]
        new_zip = plugin_zip(version="0.2.0", permissions=permissions, storage_mb=10)
        new = version_entry(self.github, self.repo, "0.2.0", new_zip,
                            permissions=permissions, storage_mb=10)
        icon = {"icons/hindsight-garden.png": PNG}

        report = check(files([plugin_entry(old)], **icon), files([plugin_entry(new, old)], **icon),
                       self.github)

        self.assertEqual(report.problems, [])
        notes = "\n".join(report.notes)
        self.assertIn("new permissions: island", notes)
        self.assertIn("10 MB", notes)
        self.assertIn("/compare/0.1.0...0.2.0", notes)
        self.assertNotIn("third-party", notes)
        self.assertEqual(self.github.downloaded, [new["url"]])

    # 没改的插件不检查：别人的旧条目不拖累这个 PR
    def test_skips_plugins_that_did_not_change(self):
        broken = self.new_plugin()
        broken["description"] = {}
        repo = "someone/garden-two"
        data = plugin_zip(plugin_id="garden-two")
        garden = plugin_entry(version_entry(self.github, repo, "0.1.0", data),
                              plugin_id="garden-two", repo=repo)
        icon = {"icons/garden-two.png": PNG}

        report = check(files([broken]), files([broken, garden], **icon), self.github)

        self.assertEqual(report.problems, [])

    # 同一个 id 出现两次
    def test_reports_a_duplicate_id(self):
        garden = self.new_plugin()
        head = files([garden, garden], **{"icons/hindsight-garden.png": PNG})

        problems = check(files(), head, self.github).problems

        self.assertEqual(len(problems), 1)
        self.assertIn("more than one entry", problems[0])

    # PR 改了清单以外的文件，或者加了不属于任何插件的图标
    def test_reports_files_outside_the_list(self):
        head = files(**{"README.md": "changed", "icons/nobody.png": PNG})

        problems = check(files(), head, self.github).problems

        self.assertEqual(len(problems), 2)
        self.assertIn("`README.md`", problems[0])
        self.assertIn("`icons/nobody.png`", problems[1])

    # 作者和仓库主人不是同一个人：提醒审核者确认
    def test_notes_an_author_who_is_not_the_owner(self):
        garden = self.new_plugin()
        head = files([garden], **{"icons/hindsight-garden.png": PNG})

        notes = "\n".join(check(files(), head, self.github, author="stranger").notes)

        self.assertIn("`stranger` opened this pull request", notes)

    # PR 里的值进报告时包在代码里：不会变成链接、图片或 @提醒
    def test_shows_values_from_the_pull_request_as_code(self):
        garden = self.new_plugin()
        garden["versions"][0]["permissions"] = ["@someone ![x](https://example.com/x.png)`"]

        problems = "\n".join(check(files(), files([garden]), self.github).problems)

        self.assertIn("`@someone ![x](https://example.com/x.png)'`", problems)


class ThemeTest(unittest.TestCase):
    def setUp(self):
        self.github = FakeGitHub()
        self.repo = "someone/hindsight-harbor"

    def new_theme(self, data=None, version="1.0.0"):
        data = data if data is not None else theme_zip(version=version)
        url = self.github.publish(self.repo, version, data)
        return {"id": "harbor", "repo": self.repo,
                "versions": [{"version": version, "url": url, "sha256": sha256(data)}]}

    # 合规的主题：没有问题；提醒审核者导入看一眼；不公开的变量告诉作者没有用
    def test_passes_a_valid_new_theme(self):
        harbor = self.new_theme(theme_zip(tokens={"--color-accent": "#3b6e8f", "--secret": "1"}))

        report = check(files(), files(themes=[harbor]), self.github)

        self.assertEqual(report.problems, [])
        notes = "\n".join(report.notes)
        self.assertIn("`--secret`", notes)
        self.assertIn("Import", notes)

    # theme.json 违反 Hindsight 的规则：名字太长、变量值带分号、id 对不上
    def test_reports_a_theme_json_that_breaks_the_rules(self):
        cases = [
            ({"name": "x" * 65}, "longer than 64"),
            ({"tokens": {"--color-accent": "red; color: blue"}}, "`--color-accent`"),
            ({"layout": "grid"}, "`layout`"),
        ]
        for fields, text in cases:
            with self.subTest(text):
                self.github = FakeGitHub()
                harbor = self.new_theme(theme_zip(**fields))
                problems = check(files(), files(themes=[harbor]), self.github).problems
                self.assertEqual(len(problems), 1, problems)
                self.assertIn(text, problems[0])

    # 新版本没放在 versions 第一个：网站只显示第一个
    def test_reports_a_new_version_that_is_not_first(self):
        harbor = self.new_theme()
        newer = self.new_theme(version="1.1.0")
        harbor["versions"].append(newer["versions"][0])

        problems = check(files(), files(themes=[harbor]), self.github).problems

        self.assertEqual(len(problems), 1)
        self.assertIn("first", problems[0])


class CssTest(unittest.TestCase):
    # 从网上加载东西的写法都报出来，转义写的也一样；data: 地址可以
    def test_reports_css_that_loads_files(self):
        for css in (
            "body { background: url(https://example.com/a.png) }",
            "body { background: URL( 'http://example.com/a.png') }",
            "body { background: u\\72l(https://example.com/a.png) }",
            "@import 'other.css';",
            "@\\69mport 'other.css';",
            "body { background: image-set('a.png' 1x) }",
            "@font-face { src: url(font.woff2) }",
        ):
            with self.subTest(css):
                self.assertNotEqual(theme_css_problems(css), [])

    def test_allows_css_without_files(self):
        for css in (
            "[data-part='card'] { border: 0; }",
            "body { background: url(data:image/png;base64,AAAA) }",
            "body { background: image-set(url('data:image/png;base64,AAAA') 1x) }",
            "p::before { content: '\\201C'; }",
        ):
            with self.subTest(css):
                self.assertEqual(theme_css_problems(css), [])


if __name__ == "__main__":
    unittest.main()
