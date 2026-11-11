#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exercise certification matching and fail-closed PR metadata validation."""

import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("dco", ROOT / "scripts/checks/check-dco.py")
DCO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DCO)


def commit(message="Change\n\nSigned-off-by: Example Author <author@example.com>\n", index=1):
    return {"sha": f"{index:040x}", "commit": {"message": message, "author": {
        "name": "Example Author", "email": "author@example.com",
    }}}


class CertificationTests(unittest.TestCase):
    def test_matching_author_and_coauthor(self):
        item = commit("Change\n\nCo-authored-by: Example Coauthor <co@example.com>\n"
                      "Signed-off-by: Example Author <AUTHOR@example.com>\n"
                      "Signed-off-by: Example Coauthor <co@example.com>\n")
        self.assertEqual(DCO.commit_errors(item), [])

    def test_missing_or_mismatched_signoff(self):
        for message in ["Change", "Change\n\nSigned-off-by: Different Author <author@example.com>\n",
                        "Change\n\nSigned-off-by: Example Author <other@example.com>\n"]:
            with self.subTest(message=message):
                self.assertTrue(DCO.commit_errors(commit(message)))

    def test_body_text_is_not_a_signoff(self):
        self.assertTrue(DCO.commit_errors(commit(
            "Change\n\nSigned-off-by: Example Author <author@example.com>\n\n"
            "This is body prose following a quoted example, not a trailer.\n")))

    def test_unsigned_and_malformed_coauthor(self):
        for trailer in ["Co-authored-by: Example Coauthor <co@example.com>",
                        "Co-authored-by: malformed", "Signed-off-by: malformed"]:
            with self.subTest(trailer=trailer):
                item = commit()
                item["commit"]["message"] += trailer + "\n"
                self.assertTrue(DCO.commit_errors(item))

    def test_merge_and_bot_authors_are_not_exempt(self):
        for name in ["Example Author", "example[bot]"]:
            item = commit("Merge branch 'example'\n")
            item["commit"]["author"]["name"] = name
            item["parents"] = [{"sha": "a" * 40}, {"sha": "b" * 40}]
            self.assertTrue(DCO.commit_errors(item))


class PullRequestTests(unittest.TestCase):
    def check(self, commits, *, count=None, head=None, after=None, pages=None):
        head = head or commits[-1]["sha"]
        metadata = {"head": {"sha": head}, "base": {"sha": "b" * 40},
                    "commits": len(commits) if count is None else count}
        calls = []

        def api(path):
            calls.append(path)
            if path == "pulls/1":
                return copy.deepcopy(after if calls.count(path) > 1 and after else metadata)
            page = int(path.rsplit("=", 1)[1])
            return (pages or {}).get(page, commits[(page - 1) * 100:page * 100])

        result = DCO.inspect_pull_request(api, 1, head)
        return result, calls

    def test_all_pages_checked_including_unsigned_middle_commit(self):
        commits = [commit(index=i) for i in range(1, 251)]
        commits[150]["commit"]["message"] = "Unsigned change\n"
        failures, calls = self.check(commits)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0][0], commits[150]["sha"])
        self.assertIn("pulls/1/commits?per_page=100&page=3", calls)

    def test_signed_commits_pass(self):
        self.assertEqual(self.check([commit()])[0], [])

    def test_oversized_or_empty_pr_fails(self):
        for count in [0, 251]:
            with self.subTest(count=count), self.assertRaises(ValueError):
                self.check([commit()], count=count)

    def test_truncated_duplicate_or_wrong_head_list_fails(self):
        for items, count, head in [([commit()], 2, None),
                                   ([commit(), commit()], 2, None),
                                   ([commit()], 1, "f" * 40)]:
            with self.subTest(count=count, head=head), self.assertRaises(ValueError):
                self.check(items, count=count, head=head)

    def test_head_changed_before_check_fails(self):
        with self.assertRaises(ValueError):
            DCO.inspect_pull_request(lambda _: {"head": {"sha": "b" * 40}}, 1, "a" * 40)

    def test_head_base_or_count_changed_during_check_fails(self):
        initial = {"head": {"sha": commit()["sha"]}, "base": {"sha": "b" * 40}, "commits": 1}
        for key, value in [("head", {"sha": "f" * 40}), ("base", {"sha": "f" * 40}), ("commits", 2)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check([commit()], after=initial | {key: value})


if __name__ == "__main__":
    unittest.main()
