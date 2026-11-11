#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Plan, apply, and verify a GitHub.com repository's open-source settings.

Uses the current gh authentication. Only apply performs remote writes; it reads
the current state again, saves a backup, and verifies the result. No project
code or configuration-supplied command is executed.
"""

import argparse
import base64
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
RULESET_NAME = "open-source-template/default-branch"
API_VERSION = "2026-03-10"
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
WORKFLOWS = (".github/workflows/dco.yml", ".github/workflows/secret-scan.yml",
             ".github/workflows/repository-files.yml")


class SetupError(Exception):
    pass


class APIError(SetupError):
    def __init__(self, method, path, status, data):
        self.status = status
        message = data.get("message", "Request failed") if isinstance(data, dict) else "Request failed"
        super().__init__(f"{method} {path}: HTTP {status}: {json.dumps(str(message)[:300])}")


class GitHub:
    def request(self, method, path, payload=None, accepted=()):
        command = ["gh", "api", "--hostname", "github.com", "--method", method,
                   "--include", "-H", "Accept: application/vnd.github+json",
                   "-H", f"X-GitHub-Api-Version: {API_VERSION}", path]
        if payload is not None:
            command += ["--input", "-"]
        env = dict(os.environ, GH_PROMPT_DISABLED="1", GH_PAGER="cat", NO_COLOR="1")
        for name in ("GH_DEBUG", "GH_REPO", "GH_HOST"):
            env.pop(name, None)
        try:
            result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                                    capture_output=True, text=True, env=env, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise SetupError("Could not run gh. Check installation, authentication, and connectivity.") from error
        # gh --include prints HTTP headers before the JSON, including on errors.
        output = result.stdout.replace("\r\n", "\n")
        match = re.search(r"(?:^|\n)HTTP/[\d.]+ (\d{3})[^\n]*\n", output)
        if not match:
            raise SetupError("gh returned no HTTP response. Check gh auth status and connectivity.")
        status = int(match[1])
        boundary = output.find("\n\n", match.start())
        if boundary < 0:
            raise SetupError("gh returned an incomplete HTTP response.")
        body = output[boundary + 2:].strip()
        try:
            data = json.loads(body) if body else None
        except json.JSONDecodeError as error:
            raise SetupError("GitHub returned a non-JSON response.") from error
        if status not in accepted and not 200 <= status < 300:
            raise APIError(method, path, status, data)
        if result.returncode and 200 <= status < 300:
            raise SetupError("gh failed despite a successful HTTP response; refusing to assume success.")
        return status, data

    def get(self, path, accepted=()):
        return self.request("GET", path, accepted=accepted)

    def pages(self, path, key=None):
        result = []
        separator = "&" if "?" in path else "?"
        for page in range(1, 101):
            _, data = self.get(f"{path}{separator}per_page=100&page={page}")
            items = data[key] if key else data
            if not isinstance(items, list):
                raise SetupError("GitHub returned an invalid paginated response.")
            result.extend(items)
            if len(items) < 100:
                return result
        raise SetupError("GitHub pagination exceeded the limit; refusing an incomplete inventory.")


def git(project, *args):
    try:
        return subprocess.check_output(["git", "-C", str(project), *args], text=True,
                                       stderr=subprocess.DEVNULL, timeout=15).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        raise SetupError("Cannot identify the project from Git. Use --project or --repo explicitly.") from error


def repository_name(value):
    if not isinstance(value, str) or not REPOSITORY.fullmatch(value) or value in {"OWNER/REPO"}:
        raise SetupError("Repository must be a real GitHub OWNER/REPO name.")
    if any(part in {".", ".."} for part in value.split("/")):
        raise SetupError("Invalid repository name.")
    return value


def remote_repository(value):
    match = re.fullmatch(r"git@github\.com:([^\s]+)", value)
    if match:
        path = match[1]
    else:
        parsed = urlsplit(value)
        if (parsed.scheme not in {"https", "ssh"}
                or parsed.hostname not in {"github.com", "ssh.github.com"}
                or parsed.query or parsed.fragment):
            raise SetupError("Cannot resolve this remote to GitHub.com; use --repo OWNER/REPO.")
        path = parsed.path.lstrip("/")
    return repository_name(path.removesuffix(".git"))


def resolve_target(project=None, repo=None):
    if repo:
        return repository_name(repo), None
    root = Path(git(project or Path.cwd(), "rev-parse", "--show-toplevel"))
    remotes = git(root, "remote").splitlines()
    remote = "origin" if "origin" in remotes else remotes[0] if len(remotes) == 1 else None
    if remote is None:
        raise SetupError("No unambiguous Git remote. Specify --repo OWNER/REPO.")
    urls = git(root, "remote", "get-url", "--all", remote).splitlines()
    urls += git(root, "remote", "get-url", "--push", "--all", remote).splitlines()
    names = {remote_repository(url).lower(): remote_repository(url) for url in urls}
    if len(names) != 1:
        raise SetupError("Fetch and push targets differ. Specify --repo OWNER/REPO.")
    return next(iter(names.values())), root


def merge_known(base, overrides, location="overrides"):
    if not isinstance(overrides, dict):
        raise SetupError(f"{location} must be an object.")
    result = copy.deepcopy(base)
    for key, value in overrides.items():
        if key not in base:
            raise SetupError(f"Unknown setting: {location}.{key}")
        if isinstance(base[key], dict):
            result[key] = merge_known(base[key], value, f"{location}.{key}")
        else:
            result[key] = value
    return result


def validate_checks(checks):
    if not isinstance(checks, list):
        raise SetupError("Checks must be a list of context/app_slug objects.")
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"context", "app_slug"}:
            raise SetupError("Each check needs exactly context and app_slug.")
        name, slug = check["context"], check["app_slug"]
        if (not isinstance(name, str) or not name.strip() or len(name) > 200
                or name != name.strip() or any(ord(c) < 32 for c in name)
                or "REPLACE" in name or "{{" in name):
            raise SetupError("Replace check placeholders with exact GitHub check names.")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
            raise SetupError("Each check needs a valid GitHub App slug.")
    if len({item["context"] for item in checks}) != len(checks):
        raise SetupError("Required check names must be unique.")


def load_settings(path=None, profile=None, target=None):
    data = json.loads(Path(path).read_text()) if path else {}
    allowed = {"version", "profile", "repository", "new_repository", "documentation_only",
               "project_checks", "overrides"}
    if not isinstance(data, dict) or set(data) - allowed:
        raise SetupError("Unknown project configuration fields.")
    if type(data.get("version", 1)) is not int or data.get("version", 1) != 1:
        raise SetupError("Only configuration version 1 is supported.")
    if data.get("repository") is not None:
        pin = repository_name(data["repository"])
        if pin.lower() != target.lower():
            raise SetupError("Configured repository does not match the selected target.")
    selected = profile or data.get("profile", "solo")
    if selected not in {"solo", "team"}:
        raise SetupError("Profile must be solo or team.")
    settings = json.loads((ROOT / "github/profiles/solo.json").read_text())
    if selected == "team":
        settings = merge_known(settings, json.loads((ROOT / "github/profiles/team.json").read_text()))
    overrides = data.get("overrides", {})
    if not isinstance(overrides, dict):
        raise SetupError("overrides must be an object.")
    if "required_checks" in overrides:
        raise SetupError("Baseline checks cannot be replaced; use project_checks to add checks.")
    settings = merge_known(settings, overrides)
    for field in ("new_repository", "documentation_only"):
        if type(data.get(field, False)) is not bool:
            raise SetupError(f"{field} must be a boolean.")
        settings[field] = data.get(field, False)
    for key, value in settings["repository_settings"].items():
        if key in {"description", "homepage"}:
            if value is not None and (not isinstance(value, str) or len(value) > 350):
                raise SetupError(f"{key} must be null or a string of at most 350 characters.")
            if key == "homepage" and value and urlsplit(value).scheme not in {"https", "http"}:
                raise SetupError("homepage must be an HTTP(S) URL.")
        elif value is None and key in {"has_discussions", "has_wiki", "has_projects"}:
            if settings["new_repository"]:
                settings["repository_settings"][key] = False
        elif type(value) is not bool:
            raise SetupError(f"{key} must be a boolean.")
    if not any(settings["repository_settings"][f"allow_{method}_merge" if method != "merge" else "allow_merge_commit"]
               for method in ("merge", "squash", "rebase")):
        raise SetupError("At least one merge method must be enabled.")
    for key, value in settings["reviews"].items():
        if key == "required_approving_review_count":
            if type(value) is not int or not 0 <= value <= 10:
                raise SetupError("Approval count must be an integer from 0 to 10.")
        elif type(value) is not bool:
            raise SetupError(f"{key} must be a boolean.")
    if type(settings["strict_required_status_checks_policy"]) is not bool:
        raise SetupError("strict_required_status_checks_policy must be a boolean.")
    if settings["actions"] != {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}:
        raise SetupError("This tool supports read-only Actions defaults without PR approval permission.")
    for key, value in settings["security"].items():
        if key.startswith("secret_scanning"):
            if value not in {"if_available", "preserve"}:
                raise SetupError(f"{key} must be if_available or preserve.")
        elif type(value) is not bool:
            raise SetupError(f"{key} must be a boolean.")
    project_checks = data.get("project_checks", [])
    validate_checks(project_checks)
    settings["required_checks"] += project_checks
    validate_checks(settings["required_checks"])
    settings["has_project_checks"] = bool(project_checks)
    settings["profile"] = selected
    return settings


def contains(current, desired):
    """Ignore unrelated response fields, but require every desired value."""
    if isinstance(desired, dict):
        return isinstance(current, dict) and all(k in current and contains(current[k], v)
                                                for k, v in desired.items())
    if isinstance(desired, list):
        return (isinstance(current, list) and len(current) == len(desired)
                and all(any(contains(item, want) for item in current) for want in desired))
    return type(current) is type(desired) and current == desired


def change(plan, label, current, desired, method, path, payload=None):
    if contains(current, desired):
        plan["compliant"].append(label)
    else:
        plan["changes"].append({"setting": label, "before": current, "after": desired,
                                "method": method, "path": path,
                                "payload": desired if payload is None else payload})


def content(api, base, path, branch):
    status, data = api.get(f"{base}/contents/{path}?ref={quote(branch, safe='')}", accepted=(404,))
    if status == 404:
        return None
    if data.get("type") != "file" or data.get("encoding") != "base64":
        raise SetupError(f"Cannot inspect {path} on the default branch.")
    return base64.b64decode(data["content"]).decode("utf-8")


def discover_checks(api, base, branch, checks, existing, check_refs, now):
    """Bind checks to installed App IDs; new bindings require recent success."""
    previous = {}
    for rule in (existing or {}).get("rules", []):
        if rule["type"] == "required_status_checks":
            previous = {c["context"]: c.get("integration_id")
                        for c in rule["parameters"]["required_status_checks"]}
    apps = {}
    for slug in {c["app_slug"] for c in checks}:
        _, app = api.get(f"apps/{slug}")
        if app.get("slug") != slug or type(app.get("id")) is not int:
            raise SetupError(f"Cannot resolve check provider {slug}.")
        apps[slug] = app["id"]
    needed = [c for c in checks if previous.get(c["context"]) != apps[c["app_slug"]]]
    evidence = set()
    if needed:
        refs = [branch, *check_refs]
        _, prs = api.get(f"{base}/pulls?state=all&base={quote(branch, safe='')}&sort=updated&direction=desc&per_page=10")
        for pr in prs:
            refs.extend([pr["head"]["sha"], pr.get("merge_commit_sha")])
        for ref in dict.fromkeys(ref for ref in refs if ref):
            for run in api.pages(f"{base}/commits/{quote(ref, safe='')}/check-runs?filter=latest", "check_runs"):
                if run.get("conclusion") != "success" or not run.get("completed_at"):
                    continue
                when = datetime.fromisoformat(run["completed_at"].replace("Z", "+00:00"))
                if not now - timedelta(days=7) <= when <= now + timedelta(minutes=5):
                    continue
                app = run.get("app") or {}
                if apps.get(app.get("slug")) == app.get("id"):
                    evidence.add((run["name"], app["id"]))
            if all((c["context"], apps[c["app_slug"]]) in evidence for c in needed):
                break
    missing = [c["context"] for c in needed if (c["context"], apps[c["app_slug"]]) not in evidence]
    if missing:
        raise SetupError("Run these checks successfully within the last seven days before requiring them: "
                         + ", ".join(missing) + ". Use --check-ref for another commit or branch.")
    return [{"context": c["context"], "integration_id": apps[c["app_slug"]]} for c in checks]


def plan_rules(api, base, repo, settings, plan, check_refs, now):
    branch = repo["default_branch"]
    all_rulesets = api.pages(f"{base}/rulesets?includes_parents=true")
    managed = [r for r in all_rulesets if r["name"] == RULESET_NAME
               and r.get("source_type") == "Repository"
               and r.get("source", "").lower() == repo["full_name"].lower()]
    if len(managed) > 1:
        raise SetupError("Multiple template rulesets found; resolve the duplicate IDs before applying.")
    existing = api.get(f"{base}/rulesets/{managed[0]['id']}")[1] if managed else None
    plan["notes"].append("Other repository and inherited rulesets are preserved: "
                         + str(len(all_rulesets) - len(managed)))
    effective = api.pages(f"{base}/rules/branches/{quote(branch, safe='')}")
    status, classic = api.get(f"{base}/branches/{quote(branch, safe='')}/protection", accepted=(404,))
    if status == 200:
        plan["notes"].append("Existing classic branch protection is preserved and may impose additional requirements.")
    other = [r for r in effective if not managed or r.get("ruleset_id") != managed[0]["id"]]
    linear = any(r["type"] == "required_linear_history" for r in other)
    linear |= bool(status == 200 and classic.get("required_linear_history", {}).get("enabled"))
    repo_settings = settings["repository_settings"]
    merge_methods = [method for method, key in (("merge", "allow_merge_commit"),
                     ("squash", "allow_squash_merge"), ("rebase", "allow_rebase_merge")) if repo_settings[key]]
    compatible = set(merge_methods)
    for rule in other:
        if rule["type"] == "pull_request":
            allowed = rule.get("parameters", {}).get("allowed_merge_methods")
            if allowed is not None:
                compatible.intersection_update(allowed)
    if not compatible:
        raise SetupError("Existing rulesets allow no merge method enabled by this profile. Resolve the conflict first.")
    if linear and not (repo_settings["allow_squash_merge"] or repo_settings["allow_rebase_merge"]):
        raise SetupError("Existing linear-history protection conflicts with merge-commit-only settings. "
                         "Resolve the policy conflict explicitly; existing protection will not be removed.")
    if any(r["type"] == "merge_queue" for r in other):
        raise SetupError("An existing merge queue requires separate workflow support; resolve it before applying.")
    if settings["reviews"]["require_code_owner_review"]:
        owners = next((text for path in (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")
                       if (text := content(api, base, path, branch)) is not None), "")
        if not any(line.strip() and not line.lstrip().startswith("#") for line in owners.splitlines()):
            raise SetupError("Code-owner review requires a configured CODEOWNERS file on the default branch.")
        plan["notes"].append("Confirm CODEOWNERS users/teams have repository access; file presence alone cannot prove that.")
    for path in WORKFLOWS:
        text = content(api, base, path, branch)
        if text is None or re.search(r"\{\{[A-Z][A-Z_]*\}\}", text):
            raise SetupError(f"Install and customize {path} on the default branch before applying rules.")
    if not settings["has_project_checks"] and not settings["documentation_only"]:
        raise SetupError("Configure project_checks for actual tests/builds, or explicitly set documentation_only=true.")
    bindings = discover_checks(api, base, branch, settings["required_checks"], existing, check_refs, now)
    desired = {
        "name": RULESET_NAME, "target": "branch", "enforcement": "active", "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {"type": "deletion"}, {"type": "non_fast_forward"},
            {"type": "pull_request", "parameters": settings["reviews"] | {"allowed_merge_methods": merge_methods}},
            {"type": "required_status_checks", "parameters": {
                "required_status_checks": bindings,
                "strict_required_status_checks_policy": settings["strict_required_status_checks_policy"]}},
        ],
    }
    if existing:
        # Unknown additions inside our reserved ruleset need deliberate handling.
        if {r["type"] for r in existing["rules"]} - {r["type"] for r in desired["rules"]}:
            raise SetupError("The managed ruleset contains additional rule types. Move them to a separate ruleset first.")
        current = {key: existing.get(key) for key in desired}
        path, method = f"{base}/rulesets/{existing['id']}", "PUT"
    else:
        current, path, method = None, f"{base}/rulesets", "POST"
    # This change is applied last, after repository settings and security options.
    change(plan, "Default-branch ruleset", current, desired, method, path)


def build_plan(api, target, settings, check_refs=(), now=None):
    now = now or datetime.now(timezone.utc)
    base = f"repos/{target}"
    _, repo = api.get(base)
    if repo["full_name"].lower() != target.lower():
        raise SetupError("GitHub resolved a different repository. Update the explicit target before continuing.")
    plan = {"repository": repo["full_name"], "default_branch": repo["default_branch"],
            "profile": settings["profile"], "changes": [], "compliant": [],
            "blocked": [], "unavailable": [], "notes": []}
    if not repo.get("permissions", {}).get("admin"):
        plan["blocked"].append("Repository admin access is required. Check gh authentication and token permissions.")
    if repo.get("archived"):
        plan["blocked"].append("Repository is archived; the tool will not unarchive it.")
    desired = {k: v for k, v in settings["repository_settings"].items() if v is not None}
    change(plan, "Repository preferences", {k: repo.get(k) for k in desired}, desired, "PATCH", base)

    def inspect(label, operation):
        try:
            operation()
        except SetupError as error:
            plan["blocked"].append(f"{label}: {error}")

    def actions():
        path = f"{base}/actions/permissions/workflow"
        _, current = api.get(path)
        change(plan, "Actions token permissions", current, settings["actions"], "PUT", path)
        if repo["visibility"] != "public":
            path = f"{base}/actions/permissions/fork-pr-workflows-private-repos"
            _, current = api.get(path)
            desired_fork = {"send_write_tokens_to_workflows": False, "send_secrets_and_variables": False}
            payload = {k: current[k] for k in ("run_workflows_from_fork_pull_requests",
                                               "require_approval_for_fork_pr_workflows")}
            payload.update(desired_fork)
            change(plan, "Private fork token/secret permissions", current, desired_fork, "PUT", path, payload)
        else:
            plan["notes"].append("Ordinary public fork PR workflows use GitHub's read-only/no-secrets model. "
                                 "Audit privileged pull_request_target workflows separately.")
    inspect("Actions settings", actions)

    def dependabot_alerts():
        path = f"{base}/vulnerability-alerts"
        status, _ = api.get(path, accepted=(404,))
        wanted = settings["security"]["dependabot_alerts"]
        change(plan, "Dependabot alerts", status == 204, wanted, "PUT" if wanted else "DELETE", path, {})
    inspect("Dependabot alerts", dependabot_alerts)

    def security_updates():
        path = f"{base}/automated-security-fixes"
        status, current = api.get(path, accepted=(404,))
        wanted = settings["security"]["dependabot_security_updates"]
        enabled = status == 200 and current["enabled"]
        change(plan, "Dependabot automatic security update PRs", enabled, wanted,
               "PUT" if wanted else "DELETE", path, {})
        # Version-update PRs are controlled by the committed configuration.
        configured = content(api, base, ".github/dependabot.yml", repo["default_branch"])
        if configured is None:
            configured = content(api, base, ".github/dependabot.yaml", repo["default_branch"])
        if configured is not None:
            plan["notes"].append("A Dependabot version-update configuration exists. It is preserved; "
                                 "review its PR schedule and the strict DCO policy separately.")
    inspect("Dependabot update PRs", security_updates)

    def private_reports():
        if repo["visibility"] != "public":
            plan["notes"].append("Private vulnerability reporting requires a public repository; retain the email route.")
            return
        path = f"{base}/private-vulnerability-reporting"
        _, current = api.get(path)
        wanted = settings["security"]["private_vulnerability_reporting"]
        change(plan, "Private vulnerability reporting", current["enabled"], wanted,
               "PUT" if wanted else "DELETE", path, {})
    inspect("Private reporting", private_reports)

    security = repo.get("security_and_analysis") or {}
    paid_already_enabled = any(security.get(name, {}).get("status") == "enabled"
                               for name in ("advanced_security", "secret_protection"))
    scanning_enabled = security.get("secret_scanning", {}).get("status") == "enabled"
    can_enable_scanning = repo["visibility"] == "public" or paid_already_enabled or scanning_enabled
    scanning_after_apply = scanning_enabled or (
        can_enable_scanning and settings["security"]["secret_scanning"] == "if_available")
    for feature in ("secret_scanning", "secret_scanning_push_protection"):
        if settings["security"][feature] == "preserve":
            plan["notes"].append(f"{feature}: preserving the project setting.")
            continue
        current = security.get(feature, {}).get("status")
        if current == "enabled":
            plan["compliant"].append(feature)
        elif can_enable_scanning:
            if feature == "secret_scanning_push_protection" and not scanning_after_apply:
                plan["blocked"].append("Push protection requires secret scanning. Enable scanning or "
                                       "explicitly preserve both settings.")
                continue
            change(plan, feature, {"security_and_analysis": {feature: {"status": current}}},
                   {"security_and_analysis": {feature: {"status": "enabled"}}}, "PATCH", base)
        else:
            plan["unavailable"].append(f"{feature}: private repository has no already-enabled protection "
                                        "that proves availability; no paid product will be activated.")
    inspect("Ruleset readiness", lambda: plan_rules(api, base, repo, settings, plan, check_refs, now))
    return plan


def apply_plan(api, plan):
    if plan["blocked"]:
        raise SetupError("Preflight is blocked; no settings were changed. Resolve the reported prerequisites.")
    if not plan["changes"]:
        return None
    directory = Path(tempfile.mkdtemp(prefix="github-settings-backup-"))
    backup = directory / "before-and-planned-changes.json"
    with open(backup, "x", opener=lambda path, flags: os.open(path, flags, 0o600)) as stream:
        json.dump(plan, stream, indent=2)
        stream.write("\n")
    completed = []
    for item in plan["changes"]:
        try:
            if item["setting"] == "Default-branch ruleset":
                if item["method"] == "PUT":
                    _, latest = api.get(item["path"])
                    current = {key: latest.get(key) for key in item["before"]}
                    if current != item["before"]:
                        raise SetupError("The ruleset changed during setup. Re-run plan before applying.")
                else:
                    existing = api.pages(item["path"] + "?includes_parents=false")
                    if any(r["name"] == RULESET_NAME for r in existing):
                        raise SetupError("A template ruleset was created during setup. Re-run plan.")
            api.request(item["method"], item["path"], item["payload"])
            completed.append(item["setting"])
        except SetupError as error:
            raise SetupError(f"Apply stopped: {error}. Completed: {', '.join(completed) or 'none'}. "
                             f"Backup: {backup}. Re-run plan to inspect partial changes; no rollback was attempted.") from error
    return str(backup)


def print_plan(plan, as_json=False):
    if as_json:
        print(json.dumps(plan, indent=2))
        return
    print(f"Repository: {plan['repository']} | branch: {plan['default_branch']} | profile: {plan['profile']}")
    for item in plan["changes"]:
        print(f"CHANGE: {item['setting']}")
        print("  before: " + json.dumps(item["before"], sort_keys=True))
        print("  after:  " + json.dumps(item["after"], sort_keys=True))
    for key in ("compliant", "blocked", "unavailable", "notes"):
        for message in plan[key]:
            print(f"{key.upper()}: {message}")
    print(f"Result: {len(plan['changes'])} changes, {len(plan['blocked'])} blockers, "
          f"{len(plan['unavailable'])} unavailable features.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "apply", "verify"))
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--project", type=Path, help="Destination checkout; defaults to the working directory")
    target.add_argument("--repo", help="Explicit GitHub.com OWNER/REPO, without using a local remote")
    parser.add_argument("--config", type=Path, help="Project JSON; otherwise .github/open-source-settings.json")
    parser.add_argument("--profile", choices=("solo", "team"), help="Override the configured profile")
    parser.add_argument("--check-ref", action="append", default=[], help="Additional branch or commit for check discovery")
    parser.add_argument("--json", action="store_true", help="Machine-readable plan or verification result")
    args = parser.parse_args(argv)
    target, project = resolve_target(args.project, args.repo)
    path = args.config
    if path is None and project is not None:
        candidate = project / ".github/open-source-settings.json"
        path = candidate if candidate.exists() else None
    settings = load_settings(path, args.profile, target)
    for ref in args.check_ref:
        if not ref or len(ref) > 250 or any(ord(c) < 32 for c in ref):
            raise SetupError("Invalid --check-ref.")
    api = GitHub()
    plan = build_plan(api, target, settings, args.check_ref)
    if args.command == "apply":
        # Always calculate a fresh plan; never execute a saved JSON plan as code.
        if plan["blocked"]:
            print_plan(plan, args.json)
            return 2
        backup = apply_plan(api, plan)
        try:
            plan = build_plan(api, target, settings, args.check_ref)
        except SetupError as error:
            raise SetupError(f"Changes were applied but verification failed: {error}. Backup: {backup}") from error
        if backup:
            plan["notes"].append(f"Before-state backup: {backup}")
    print_plan(plan, args.json)
    incomplete = bool(plan["blocked"] or plan["unavailable"])
    if args.command != "plan":
        incomplete |= bool(plan["changes"])
    return 2 if incomplete else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SetupError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"Setup failed: {error}", file=sys.stderr)
        raise SystemExit(1)
