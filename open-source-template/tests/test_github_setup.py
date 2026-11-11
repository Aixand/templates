# SPDX-License-Identifier: Apache-2.0
"""Exercise repository targeting, preflight, API mutations, and verification."""

import base64
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("github_setup", ROOT / "scripts/configure-github.py")
SETUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SETUP)
BASE = "repos/Aixand/example"
NOW = datetime.now(timezone.utc)


def settings(profile="solo"):
    result = SETUP.load_settings(profile=profile, target="Aixand/example")
    result["documentation_only"] = True
    return result


class FakeGitHub(SETUP.GitHub):
    """A stateful API double: applying a plan changes subsequent GET responses."""
    def __init__(self):
        self.calls = []
        self.errors = {}
        self.repo = {
            "full_name": "Aixand/example", "default_branch": "main", "visibility": "public",
            "permissions": {"admin": True}, "archived": False,
            "allow_merge_commit": True, "allow_squash_merge": True, "allow_rebase_merge": True,
            "allow_auto_merge": False, "delete_branch_on_merge": False, "has_issues": True,
            "has_wiki": True, "has_projects": True, "has_discussions": True,
            "description": "Existing description", "homepage": "https://example.com", "has_pull_requests": True,
            "security_and_analysis": {
                "secret_scanning": {"status": "disabled"},
                "secret_scanning_push_protection": {"status": "disabled"},
            },
        }
        self.rulesets = []
        self.classic = None
        self.actions = {"default_workflow_permissions": "write", "can_approve_pull_request_reviews": True}
        self.fork = {"run_workflows_from_fork_pull_requests": True,
                     "require_approval_for_fork_pr_workflows": True,
                     "send_write_tokens_to_workflows": True, "send_secrets_and_variables": True}
        self.alerts = False
        self.updates = True
        self.reporting = False
        self.files = {path: "name: Installed workflow\n" for path in SETUP.WORKFLOWS}
        self.prs = []
        self.checks = [
            {"name": c["context"], "conclusion": "success", "completed_at": NOW.isoformat(),
             "app": {"id": 15368, "slug": "github-actions"}}
            for c in settings()["required_checks"]
        ]

    @property
    def writes(self):
        return [item for item in self.calls if item[0] != "GET"]

    def request(self, method, path, payload=None, accepted=()):
        self.calls.append((method, path, copy.deepcopy(payload)))
        clean = urlsplit(path).path
        if (method, clean) in self.errors:
            raise SETUP.APIError(method, path, self.errors[method, clean], {"message": "Denied"})
        status, data = 200, None
        if method == "GET":
            if clean == BASE:
                data = self.repo
            elif clean == "apps/github-actions":
                data = {"id": 15368, "slug": "github-actions"}
            elif clean == BASE + "/rulesets":
                data = self.rulesets
            elif clean.startswith(BASE + "/rulesets/"):
                data = next(r for r in self.rulesets if r["id"] == int(clean.rsplit("/", 1)[1]))
            elif "/rules/branches/" in clean:
                data = [rule | {"ruleset_id": r["id"]} for r in self.rulesets for rule in r["rules"]]
            elif clean.endswith("/protection"):
                status, data = (200, self.classic) if self.classic else (404, None)
            elif clean.endswith("/actions/permissions/workflow"):
                data = self.actions
            elif clean.endswith("/actions/permissions/fork-pr-workflows-private-repos"):
                data = self.fork
            elif clean.endswith("/vulnerability-alerts"):
                status = 204 if self.alerts else 404
            elif clean.endswith("/automated-security-fixes"):
                data = {"enabled": self.updates, "paused": False}
            elif clean.endswith("/private-vulnerability-reporting"):
                data = {"enabled": self.reporting}
            elif "/contents/" in clean:
                text = self.files.get(unquote(clean.split("/contents/", 1)[1]))
                if text is None:
                    status = 404
                else:
                    data = {"type": "file", "encoding": "base64",
                            "content": base64.b64encode(text.encode()).decode()}
            elif clean.endswith("/pulls"):
                data = self.prs
            elif clean.endswith("/check-runs"):
                data = {"check_runs": self.checks}
            else:
                raise AssertionError((method, path))
        elif method == "PATCH" and clean == BASE:
            for key, value in payload.items():
                if key == "security_and_analysis":
                    self.repo[key].update(value)
                else:
                    self.repo[key] = value
        elif method == "PUT" and clean.endswith("/actions/permissions/workflow"):
            self.actions.update(payload)
        elif method == "PUT" and clean.endswith("/actions/permissions/fork-pr-workflows-private-repos"):
            self.fork.update(payload)
        elif clean.endswith("/vulnerability-alerts"):
            self.alerts = method == "PUT"
        elif clean.endswith("/automated-security-fixes"):
            self.updates = method == "PUT"
        elif clean.endswith("/private-vulnerability-reporting"):
            self.reporting = method == "PUT"
        elif clean == BASE + "/rulesets" and method == "POST":
            self.rulesets.append(copy.deepcopy(payload) | {"id": 101, "source_type": "Repository",
                                                          "source": "Aixand/example"})
        elif "/rulesets/" in clean and method == "PUT":
            existing = next(r for r in self.rulesets if r["id"] == int(clean.rsplit("/", 1)[1]))
            existing.update(copy.deepcopy(payload))
        else:
            raise AssertionError((method, path, payload))
        if status >= 400 and status not in accepted:
            raise SETUP.APIError(method, path, status, data)
        return status, copy.deepcopy(data)


class ConfigurationTests(unittest.TestCase):
    def load(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps(data))
            return SETUP.load_settings(path, target="Aixand/example")

    def test_profiles_and_project_overrides(self):
        solo, team = settings(), settings("team")
        self.assertEqual(solo["reviews"]["required_approving_review_count"], 0)
        self.assertEqual(team["reviews"]["required_approving_review_count"], 1)
        self.assertTrue(team["reviews"]["dismiss_stale_reviews_on_push"])
        result = self.load({"overrides": {"repository_settings": {"allow_squash_merge": True}}})
        self.assertTrue(result["repository_settings"]["allow_squash_merge"])
        self.assertFalse(result["repository_settings"]["allow_rebase_merge"])

    def test_new_repositories_disable_unused_features(self):
        self.assertIsNone(self.load({})["repository_settings"]["has_wiki"])
        for key in ["has_wiki", "has_projects", "has_discussions"]:
            self.assertIs(self.load({"new_repository": True})["repository_settings"][key], False)

    def test_rejects_unknown_or_dangerous_settings(self):
        for data in [
            {"version": True}, {"profile": "missing"}, {"repository": "Aixand/other"},
            {"repository": "OWNER/REPO"}, {"documentation_only": "false"},
            {"overrides": {"repository_settings": {"visibility": "public"}}},
            {"overrides": {"repository_settings": {"allow_auto_merge": "false"}}},
            {"overrides": {"repository_settings": {"homepage": "javascript:alert(1)"}}},
            {"overrides": {"reviews": {"required_approving_review_count": True}}},
            {"overrides": {"required_checks": []}},
            {"overrides": {"actions": {"default_workflow_permissions": "write"}}},
            {"overrides": {"security": {"advanced_security": True}}},
            {"project_checks": [{"context": "REPLACE ME", "app_slug": "github-actions"}]},
            {"project_checks": [{"context": "DCO sign-off", "app_slug": "github-actions"}]},
        ]:
            with self.subTest(data=data), self.assertRaises(SETUP.SetupError):
                self.load(data)

    def test_remote_formats_and_rejections(self):
        for remote in ["git@github.com:Aixand/example.git", "https://github.com/Aixand/example.git",
                       "ssh://git@ssh.github.com:443/Aixand/example.git"]:
            self.assertEqual(SETUP.remote_repository(remote), "Aixand/example")
        for remote in ["git@gitlab.com:Aixand/example.git", "https://github.com/x/y/other", "file:///x/y"]:
            with self.subTest(remote=remote), self.assertRaises(SETUP.SetupError):
                SETUP.remote_repository(remote)

    def test_target_uses_git_not_gh_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(["git", "init", "-q", directory], check=True)
            subprocess.run(["git", "-C", directory, "remote", "add", "origin",
                            "git@github.com:Aixand/example.git"], check=True)
            with patch.dict(os.environ, {"GH_REPO": "Aixand/wrong"}):
                target, root = SETUP.resolve_target(Path(directory))
            self.assertEqual(target, "Aixand/example")
            self.assertEqual(root, Path(directory))
            subprocess.run(["git", "-C", directory, "remote", "set-url", "--push", "origin",
                            "git@github.com:Aixand/other.git"], check=True)
            with self.assertRaises(SETUP.SetupError):
                SETUP.resolve_target(Path(directory))
            self.assertEqual(SETUP.resolve_target(repo="Aixand/explicit"), ("Aixand/explicit", None))


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeGitHub()
        self.settings = settings()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Exercise real restrictive backup creation without leaving test artifacts.
        self.backup_patch = patch.object(SETUP.tempfile, "mkdtemp", return_value=self.temp.name)
        self.backup_patch.start()
        self.addCleanup(self.backup_patch.stop)

    def plan(self):
        return SETUP.build_plan(self.api, "Aixand/example", self.settings, now=NOW)

    def test_plan_is_read_only_and_preserves_project_preferences(self):
        plan = self.plan()
        self.assertFalse(plan["blocked"])
        self.assertFalse(self.api.writes)
        payload = plan["changes"][0]["payload"]
        for key in ["visibility", "default_branch", "has_wiki", "has_discussions", "has_projects",
                    "description", "homepage"]:
            self.assertNotIn(key, payload)
        rules = plan["changes"][-1]
        self.assertEqual(rules["setting"], "Default-branch ruleset")
        self.assertEqual(rules["payload"]["bypass_actors"], [])
        self.assertEqual(rules["payload"]["conditions"]["ref_name"]["include"], ["~DEFAULT_BRANCH"])

    def test_apply_then_verify_is_idempotent(self):
        backup = SETUP.apply_plan(self.api, self.plan())
        self.assertEqual(Path(backup).stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(Path(backup).read_text())["repository"], "Aixand/example")
        self.assertTrue(self.api.writes[-1][1].endswith("/rulesets"))
        self.assertEqual(len(self.api.rulesets), 1)
        self.assertTrue(self.api.repo["has_wiki"])
        verification = self.plan()
        self.assertFalse(verification["blocked"])
        self.assertFalse(verification["changes"])
        previous_writes = len(self.api.writes)
        SETUP.apply_plan(self.api, verification)
        self.assertEqual(len(self.api.writes), previous_writes)

    def test_update_uses_existing_id_and_preserves_foreign_rules(self):
        foreign = {"id": 99, "name": "Company policy", "source_type": "Organization",
                   "source": "Aixand", "rules": [{"type": "required_signatures"}]}
        self.api.rulesets.append(copy.deepcopy(foreign))
        SETUP.apply_plan(self.api, self.plan())
        self.settings = settings("team")
        plan = self.plan()
        rules = next(c for c in plan["changes"] if c["setting"] == "Default-branch ruleset")
        self.assertEqual(rules["method"], "PUT")
        self.assertTrue(rules["path"].endswith("/101"))
        self.assertEqual(self.api.rulesets[0], foreign)

    def test_ruleset_drift_is_reported(self):
        SETUP.apply_plan(self.api, self.plan())
        self.api.rulesets[0]["bypass_actors"] = [{"actor_type": "OrganizationAdmin", "bypass_mode": "always"}]
        plan = self.plan()
        self.assertTrue(any(c["setting"] == "Default-branch ruleset" for c in plan["changes"]))

    def test_missing_workflow_prevents_all_writes(self):
        self.api.files.clear()
        plan = self.plan()
        self.assertTrue(plan["blocked"])
        with self.assertRaises(SETUP.SetupError):
            SETUP.apply_plan(self.api, plan)
        self.assertFalse(self.api.writes)

    def test_application_projects_need_actual_project_checks(self):
        self.settings["documentation_only"] = False
        self.assertIn("project_checks", " ".join(self.plan()["blocked"]))

    def test_recent_success_from_expected_app_is_required(self):
        original = copy.deepcopy(self.api.checks)
        for mutation in [
            {"app": {"id": 999, "slug": "github-actions"}},
            {"app": {"id": 15368, "slug": "other-app"}},
            {"conclusion": "skipped"}, {"conclusion": "failure"},
            {"completed_at": (NOW - timedelta(days=8)).isoformat()},
        ]:
            with self.subTest(mutation=mutation):
                self.api.checks = copy.deepcopy(original)
                self.api.checks[0].update(mutation)
                self.assertTrue(self.plan()["blocked"])
        self.assertFalse(self.api.writes)

    def test_existing_bindings_do_not_expire_on_idle_repositories(self):
        SETUP.apply_plan(self.api, self.plan())
        self.api.checks.clear()
        self.assertFalse(self.plan()["blocked"])

    def test_unknown_managed_rules_and_duplicates_block_replacement(self):
        SETUP.apply_plan(self.api, self.plan())
        self.api.rulesets[0]["rules"].append({"type": "required_signatures"})
        self.assertIn("additional rule types", " ".join(self.plan()["blocked"]))
        self.api.rulesets.append(copy.deepcopy(self.api.rulesets[0]))
        self.assertIn("Multiple", " ".join(self.plan()["blocked"]))

    def test_inherited_name_is_not_adopted(self):
        self.api.rulesets = [{"id": 99, "name": SETUP.RULESET_NAME, "source_type": "Organization",
                              "source": "Aixand", "rules": []}]
        plan = self.plan()
        self.assertEqual(plan["changes"][-1]["method"], "POST")

    def test_conflicting_existing_protection_blocks_changes(self):
        self.api.classic = {"required_linear_history": {"enabled": True}}
        self.assertIn("linear-history", " ".join(self.plan()["blocked"]))
        self.api.classic = None
        self.api.rulesets = [{"id": 99, "name": "queue", "source_type": "Organization",
                              "source": "Aixand", "rules": [{"type": "merge_queue"}]}]
        self.assertIn("merge queue", " ".join(self.plan()["blocked"]))

    def test_inherited_merge_method_conflict_blocks_setup(self):
        self.api.rulesets = [{"id": 99, "name": "squash only", "source_type": "Organization",
                              "source": "Aixand", "rules": [{"type": "pull_request",
                              "parameters": {"allowed_merge_methods": ["squash"]}}]}]
        self.assertIn("no merge method", " ".join(self.plan()["blocked"]))
        self.assertFalse(self.api.writes)

    def test_private_features_and_fork_permission_preservation(self):
        self.api.repo["visibility"] = "private"
        plan = self.plan()
        self.assertEqual(len(plan["unavailable"]), 2)
        self.assertFalse(any(c["setting"] == "Private vulnerability reporting" for c in plan["changes"]))
        SETUP.apply_plan(self.api, plan)
        self.assertTrue(self.api.fork["run_workflows_from_fork_pull_requests"])
        self.assertTrue(self.api.fork["require_approval_for_fork_pr_workflows"])
        self.assertFalse(self.api.fork["send_write_tokens_to_workflows"])
        self.assertFalse(self.api.fork["send_secrets_and_variables"])
        self.assertFalse(any("security_and_analysis" in (c[2] or {}) for c in self.api.writes))

    def test_permission_errors_do_not_become_false_compliance(self):
        self.api.errors["GET", BASE + "/actions/permissions/workflow"] = 403
        plan = self.plan()
        self.assertIn("HTTP 403", " ".join(plan["blocked"]))
        with self.assertRaises(SETUP.SetupError):
            SETUP.apply_plan(self.api, plan)
        self.assertFalse(self.api.writes)

    def test_repo_identity_and_admin_access(self):
        self.api.repo["full_name"] = "Aixand/renamed"
        with self.assertRaises(SETUP.SetupError):
            self.plan()
        self.api.repo["full_name"] = "Aixand/example"
        self.api.repo["permissions"]["admin"] = False
        self.assertIn("admin access", " ".join(self.plan()["blocked"]))

    def test_partial_failure_stops_before_ruleset_activation(self):
        self.api.errors["PUT", BASE + "/vulnerability-alerts"] = 403
        with self.assertRaisesRegex(SETUP.SetupError, "Completed: Repository preferences"):
            SETUP.apply_plan(self.api, self.plan())
        self.assertFalse(self.api.rulesets)
        self.assertFalse(self.api.repo["allow_squash_merge"])
        self.assertTrue((Path(self.temp.name) / "before-and-planned-changes.json").exists())

    def test_concurrent_ruleset_creation_is_not_duplicated(self):
        plan = self.plan()
        self.api.rulesets.append({"id": 99, "name": SETUP.RULESET_NAME, "rules": []})
        with self.assertRaisesRegex(SETUP.SetupError, "created during setup"):
            SETUP.apply_plan(self.api, plan)
        self.assertEqual(len(self.api.rulesets), 1)

    def test_code_owner_review_needs_actual_rules(self):
        self.settings["reviews"]["require_code_owner_review"] = True
        self.api.files[".github/CODEOWNERS"] = "# * @example-owner\n"
        self.assertIn("CODEOWNERS", " ".join(self.plan()["blocked"]))

    def test_push_protection_dependency_is_checked_before_writes(self):
        self.settings["security"]["secret_scanning"] = "preserve"
        self.assertIn("requires secret scanning", " ".join(self.plan()["blocked"]))
        self.assertFalse(self.api.writes)

    def test_cli_apply_verifies_and_verify_detects_later_drift(self):
        with patch.object(SETUP, "GitHub", return_value=self.api), \
                patch.object(SETUP, "load_settings", return_value=self.settings):
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                code = SETUP.main(["apply", "--repo", "Aixand/example", "--json"])
            self.assertEqual(code, 0)
            result = json.loads(output.getvalue())
            self.assertFalse(result["changes"])
            self.assertTrue(any("backup" in note for note in result["notes"]))
            self.api.repo["allow_squash_merge"] = True
            count = len(self.api.writes)
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(SETUP.main(["verify", "--repo", "Aixand/example"]), 2)
            self.assertEqual(len(self.api.writes), count)

    def test_cli_blocked_apply_is_read_only(self):
        self.api.files.clear()
        with patch.object(SETUP, "GitHub", return_value=self.api), \
                patch.object(SETUP, "load_settings", return_value=self.settings), \
                patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(SETUP.main(["apply", "--repo", "Aixand/example"]), 2)
        self.assertFalse(self.api.writes)

    def test_cli_reports_incomplete_verification_after_accepted_write(self):
        original = self.api.request

        def discard_write(method, path, payload=None, accepted=()):
            if method == "PATCH" and payload and "allow_auto_merge" in payload:
                payload = dict(payload, allow_auto_merge=False)
            return original(method, path, payload, accepted)

        with patch.object(self.api, "request", side_effect=discard_write), \
                patch.object(SETUP, "GitHub", return_value=self.api), \
                patch.object(SETUP, "load_settings", return_value=self.settings), \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(SETUP.main(["apply", "--repo", "Aixand/example", "--json"]), 2)
        result = json.loads(output.getvalue())
        self.assertTrue(any(c["setting"] == "Repository preferences" for c in result["changes"]))

    def test_existing_ruleset_changed_during_setup_is_preserved(self):
        SETUP.apply_plan(self.api, self.plan())
        self.settings = settings("team")
        plan = self.plan()
        self.api.rulesets[0]["enforcement"] = "disabled"
        # The second attempt must get its own backup file.
        (Path(self.temp.name) / "before-and-planned-changes.json").unlink()
        with self.assertRaisesRegex(SETUP.SetupError, "changed during setup"):
            SETUP.apply_plan(self.api, plan)
        self.assertEqual(self.api.rulesets[0]["enforcement"], "disabled")


class TransportTests(unittest.TestCase):
    def test_http_errors_and_auth_environment(self):
        result = subprocess.CompletedProcess([], 1, 'HTTP/2.0 403 Forbidden\r\nX-Test: yes\r\n\r\n{"message":"Denied"}', '')
        with patch.object(SETUP.subprocess, "run", return_value=result) as run:
            with patch.dict(os.environ, {"GH_DEBUG": "api", "GH_REPO": "wrong/repo", "GH_HOST": "example.com"}):
                with self.assertRaises(SETUP.APIError):
                    SETUP.GitHub().get(BASE)
            env = run.call_args.kwargs["env"]
            for name in ["GH_DEBUG", "GH_REPO", "GH_HOST"]:
                self.assertNotIn(name, env)

    def test_204_and_documented_disabled_response(self):
        for status, body, expected in [(204, "", None), (404, '{"message":"Not Found"}', {"message": "Not Found"})]:
            result = subprocess.CompletedProcess([], int(status == 404), f'HTTP/2.0 {status} Response\n\n{body}', '')
            with patch.object(SETUP.subprocess, "run", return_value=result):
                self.assertEqual(SETUP.GitHub().get(BASE, accepted=(404,)), (status, expected))

    def test_pagination_reads_every_page(self):
        api = SETUP.GitHub()
        with patch.object(api, "get", side_effect=[(200, list(range(100))), (200, [100])]) as get:
            self.assertEqual(api.pages(BASE + "/rulesets?includes_parents=true"), list(range(101)))
            self.assertIn("page=2", get.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
