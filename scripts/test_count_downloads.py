"""count_downloads.py 的测试。不联网：fetch 用假数据代替。

运行：cd scripts && python3 -m unittest test_count_downloads
"""

import unittest
import urllib.error

from count_downloads import count, fetch_with_retries, parse_url


def zip_url(repo, tag):
    return f"https://github.com/{repo}/releases/download/{tag}/{repo.split('/')[1]}-{tag}.zip"


def plugin(plugin_id, repo, *tags):
    return {
        "id": plugin_id,
        "versions": [{"version": tag, "url": zip_url(repo, tag)} for tag in tags],
    }


class CountTest(unittest.TestCase):
    # 只加列表里的 zip：同一个 release 里的 .sha256、列表里没有的旧版本都不算
    def test_sums_only_the_listed_zips(self):
        releases = {
            ("0.2.0", "pomodoro-0.2.0.zip"): 10,
            ("0.2.0", "pomodoro-0.2.0.zip.sha256"): 3,
            ("0.1.0", "pomodoro-0.1.0.zip"): 5,
            ("0.0.1", "pomodoro-0.0.1.zip"): 100,
        }

        downloads, warnings = count(
            [plugin("pomodoro", "someone/pomodoro", "0.2.0", "0.1.0")],
            lambda repo: releases,
        )

        self.assertEqual(downloads, {"pomodoro": 15})
        self.assertEqual(warnings, [])

    # 一个插件的仓库查不到，只丢掉这一个，其他插件照常统计
    def test_skips_a_plugin_whose_repo_fails(self):
        def fetch(repo):
            if repo == "gone/pomodoro":
                raise urllib.error.HTTPError(repo, 404, "Not Found", None, None)
            return {("1.0.0", "timer-1.0.0.zip"): 7}

        downloads, warnings = count(
            [
                plugin("pomodoro", "gone/pomodoro", "0.1.0"),
                plugin("timer", "someone/timer", "1.0.0"),
            ],
            fetch,
        )

        self.assertEqual(downloads, {"timer": 7})
        self.assertEqual(len(warnings), 1)
        self.assertIn("pomodoro", warnings[0])

    # 几个插件在同一个仓库里时，这个仓库只查一次；仓库名不分大小写
    def test_fetches_each_repo_once(self):
        fetched = []

        def fetch(repo):
            fetched.append(repo)
            return {("1.0.0", "tools-1.0.0.zip"): 2}

        downloads, _ = count(
            [plugin("a", "Someone/tools", "1.0.0"), plugin("b", "someone/tools", "1.0.0")],
            fetch,
        )

        self.assertEqual(fetched, ["someone/tools"])
        self.assertEqual(downloads, {"a": 2, "b": 2})

    # 某个版本的 zip 在 release 里找不到：这个版本按 0 算，插件还在结果里，并给出警告
    def test_a_missing_zip_counts_as_zero(self):
        downloads, warnings = count(
            [plugin("pomodoro", "someone/pomodoro", "0.2.0", "0.1.0")],
            lambda repo: {("0.2.0", "pomodoro-0.2.0.zip"): 4},
        )

        self.assertEqual(downloads, {"pomodoro": 4})
        self.assertEqual(len(warnings), 1)
        self.assertIn("0.1.0", warnings[0])


def failing_fetch(errors, result):
    """先依次抛出 errors 里的错误，再返回 result。calls 记下请求了几次。"""
    calls = []

    def fetch(repo):
        calls.append(repo)
        if len(calls) <= len(errors):
            raise errors[len(calls) - 1]
        return result

    return fetch, calls


def http_error(code, headers=None):
    return urllib.error.HTTPError("https://api.github.com", code, "", headers, None)


class FetchWithRetriesTest(unittest.TestCase):
    # 临时错误（503）后等第一个间隔再试，第二次成功就用第二次的结果
    def test_retries_a_temporary_error(self):
        fetch, calls = failing_fetch([http_error(503)], {"ok": 1})
        slept = []

        self.assertEqual(fetch_with_retries(fetch, "someone/pomodoro", slept.append), {"ok": 1})
        self.assertEqual(len(calls), 2)
        self.assertEqual(slept, [5])

    # 404、不是限速的 403，重试也不会变：只请求一次，错误直接抛出去
    def test_does_not_retry_other_errors(self):
        for error in [http_error(404), http_error(403, {})]:
            fetch, calls = failing_fetch([error], {"ok": 1})
            slept = []

            with self.assertRaises(urllib.error.HTTPError):
                fetch_with_retries(fetch, "someone/pomodoro", slept.append)
            self.assertEqual(len(calls), 1, error.code)
            self.assertEqual(slept, [], error.code)

    # 一直连不上：一共试 3 次，等 5 秒和 30 秒，最后一次的错误抛出去
    def test_gives_up_after_three_tries(self):
        errors = [urllib.error.URLError("offline") for _ in range(3)]
        fetch, calls = failing_fetch(errors, {"ok": 1})
        slept = []

        with self.assertRaises(urllib.error.URLError):
            fetch_with_retries(fetch, "someone/pomodoro", slept.append)
        self.assertEqual(len(calls), 3)
        self.assertEqual(slept, [5, 30])

    # 被限速时 GitHub 给了 Retry-After，就按它等；太长的等 60 秒就够
    def test_waits_as_retry_after_says(self):
        for retry_after, waited in [("2", 2), ("3600", 60)]:
            fetch, _ = failing_fetch([http_error(429, {"Retry-After": retry_after})], {"ok": 1})
            slept = []

            fetch_with_retries(fetch, "someone/pomodoro", slept.append)
            self.assertEqual(slept, [waited], retry_after)


class ParseUrlTest(unittest.TestCase):
    # release 文件的地址拆成仓库、标签、文件名；仓库名转小写，标签和文件名里的编码还原
    def test_splits_a_release_url(self):
        self.assertEqual(
            parse_url("https://github.com/Someone/Pomodoro/releases/download/v1.0%2Bfix/a%20b.zip"),
            ("someone/pomodoro", "v1.0+fix", "a b.zip"),
        )

    # 不是 GitHub release 文件的地址都不认
    def test_rejects_other_urls(self):
        for url in [
            "http://github.com/someone/pomodoro/releases/download/1.0.0/p.zip",
            "https://example.com/someone/pomodoro/releases/download/1.0.0/p.zip",
            "https://github.com/someone/pomodoro/archive/1.0.0.zip",
            "https://github.com/someone/pomodoro/releases/download/1.0.0/extra/p.zip",
        ]:
            self.assertIsNone(parse_url(url), url)


if __name__ == "__main__":
    unittest.main()
