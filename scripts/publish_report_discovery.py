"""Prepare candidate history or publish only the two permitted discovery files."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mia_capital_intelligence.discovery_catalog import (
    CATALOG_PATH, LOG_PATH, read_catalog, render_log, serialize_catalog, validate_catalog,
)

BRANCH = "automation/report-discovery"
ROOT = Path(__file__).resolve().parents[1]


class GitHub:
    """Use the job-scoped token without saving credentials or changing git configuration."""

    def __init__(self):
        self.repository = os.environ["GITHUB_REPOSITORY"]
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", self.repository):
            raise ValueError("Invalid repository name")
        self.token = os.environ["GH_TOKEN"]

    def call(self, method: str, path: str, body=None, *, missing_ok=False):
        data = json.dumps(body).encode() if body is not None else None
        endpoint = f"https://api.github.com/repos/{self.repository}" + (f"/{path}" if path else "")
        request = Request(endpoint, data=data, method=method,
                          headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                                   "Content-Type": "application/json",
                                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "MIA-Report-Discovery"})
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            if missing_ok and error.code == 404:
                return None
            if method == "POST" and path == "pulls" and error.code == 403:
                raise RuntimeError("GitHub denied PR creation. Check Settings > Actions > General > Workflow permissions > Allow GitHub Actions to create and approve pull requests.") from None
            raise RuntimeError(f"GitHub {method} {path.split('?')[0]} returned HTTP {error.code}") from None

    def history(self):
        head = self.call("GET", f"git/ref/heads/{BRANCH}", missing_ok=True)
        prs = self.call("GET", "pulls?" + urlencode({"state": "all", "head": f"{self.repository.split('/')[0]}:{BRANCH}",
                                                    "sort": "updated", "direction": "desc", "per_page": 100}))
        latest = next((pr for pr in prs if pr["state"] == "open"), prs[0] if prs else None)
        revision = head["object"]["sha"] if head else latest["head"]["sha"] if latest else None
        catalog = None
        if revision:
            content = self.call("GET", f"contents/{CATALOG_PATH}?ref={quote(revision)}", missing_ok=True)
            if content:
                catalog = json.loads(base64.b64decode(content["content"]))
                validate_catalog(catalog)
        return head, latest, catalog


def prepare(api: GitHub, output: Path) -> None:
    _, _, previous = api.history()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_catalog(previous or read_catalog(ROOT / CATALOG_PATH)), encoding="utf-8")


def commit_files(api: GitHub, files: dict[str, str], expected_head: str | None) -> str:
    """Build on current main and retain the prior automation branch as a parent."""
    if set(files) != {str(CATALOG_PATH), str(LOG_PATH)}:
        raise ValueError("Discovery publication may change only the candidate catalog and data log")
    repo = api.call("GET", "")
    default_branch = repo["default_branch"]
    if default_branch == BRANCH:
        raise ValueError("The automation branch cannot be the default branch")
    base = api.call("GET", f"git/ref/heads/{quote(default_branch, safe='')}")["object"]["sha"]
    if os.environ.get("GITHUB_SHA") and base != os.environ["GITHUB_SHA"]:
        raise ValueError("Default branch changed since checkout; rerun discovery before publication")
    base_commit = api.call("GET", f"git/commits/{base}")
    tree = api.call("POST", "git/trees", {"base_tree": base_commit["tree"]["sha"], "tree": [
        {"path": path, "mode": "100644", "type": "blob", "content": content} for path, content in files.items()
    ]})
    parents = list(dict.fromkeys([expected_head, base] if expected_head else [base]))
    commit = api.call("POST", "git/commits", {"message": "chore(data): record discovered official report versions",
                                             "tree": tree["sha"], "parents": parents})
    current = api.call("GET", f"git/ref/heads/{BRANCH}", missing_ok=True)
    if (current["object"]["sha"] if current else None) != expected_head:
        raise ValueError("Discovery branch changed during publication; rerun the scan")
    if expected_head:
        api.call("PATCH", f"git/refs/heads/{BRANCH}", {"sha": commit["sha"], "force": False})
    else:
        api.call("POST", "git/refs", {"ref": f"refs/heads/{BRANCH}", "sha": commit["sha"]})
    return commit["sha"]


def publish(api: GitHub, bundle: Path) -> dict:
    report = json.loads((bundle / "report.json").read_text())
    catalog = read_catalog(bundle / "catalog.json")
    base = read_catalog(ROOT / CATALOG_PATH)
    included = lambda data: {row["sha256"] for row in data["documents"] if row["dataset_status"] == "included"}
    if included(catalog) != included(base):
        raise ValueError("Discovery cannot add or remove published dataset versions")
    head, latest, previous = api.history()
    known_events = {row["id"] for row in (previous or base)["events"]}
    actual_new = {row["id"] for row in catalog["events"]} - known_events
    link_repair = latest and latest["state"] == "open" and any(
        event["pull_request_url"] is None for event in catalog["events"]
    )
    # Closing a proposal leaves its candidate history available for later scans.
    # An unchanged rescan must not reopen it, including after its branch is deleted.
    if not actual_new and latest and latest["state"] == "closed":
        return {"status": "unchanged_closed_proposal"}
    if not report["changed"] and not (head and latest is None) and not link_repair:
        return {"status": "unchanged"}
    if previous and not known_events.issubset({row["id"] for row in catalog["events"]}):
        raise ValueError("Discovery history changed after this scan; rerun before publication")
    # A branch without a pull request means an earlier publication stopped before PR creation.
    # Its events are already on the branch, so they are not new, but the proposal is still unposted.
    branch_without_pr = head is not None and latest is None
    if not actual_new and report["new_events"] and not link_repair and not branch_without_pr:
        return {"status": "already_published"}
    baseline_log = (ROOT / LOG_PATH).read_text(encoding="utf-8")
    open_pr = latest if latest and latest["state"] == "open" else None
    if open_pr:
        for event in catalog["events"]:
            if event["pull_request_url"] is None:
                event["pull_request_url"] = open_pr["html_url"]
    proposed_events = sum(event["pull_request_url"] in {None, open_pr["html_url"] if open_pr else None}
                          for event in catalog["events"])
    files = {str(CATALOG_PATH): serialize_catalog(catalog), str(LOG_PATH): render_log(baseline_log, catalog)}
    revision = commit_files(api, files, head["object"]["sha"] if head else None)
    run_url = f"https://github.com/{api.repository}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    body = ("## Official report discovery\n\n"
            f"This proposal records {proposed_events} file-version or source-link events. "
            "It changes the candidate catalog and public data update log. Application project and financial inputs are unchanged.\n\n"
            "The log lists each PDF, its reporting period, hash and whether that exact version is already in the dataset. "
            "New file versions remain candidates for a separate data update.\n\n"
            f"[Scan results and PDF artifacts]({run_url}) · Scan coverage: **{report['status']}**.\n\n"
            "Related to #5.\n")
    if open_pr:
        pr = api.call("PATCH", f"pulls/{open_pr['number']}", {"body": body})
    else:
        default_branch = api.call("GET", "")["default_branch"]
        pr = api.call("POST", "pulls", {"title": "chore(data): discover official airport report versions",
                                       "head": BRANCH, "base": default_branch, "body": body})
    # A newly created PR has a number only after the first commit exists.
    unlinked = [event for event in catalog["events"] if event["pull_request_url"] is None]
    if unlinked:
        for event in unlinked:
            event["pull_request_url"] = pr["html_url"]
        revision = commit_files(api, {str(CATALOG_PATH): serialize_catalog(catalog),
                                     str(LOG_PATH): render_log(baseline_log, catalog)}, revision)
    return {"status": "proposed", "pull_request": pr["html_url"], "commit": revision}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "publish"))
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()
    api = GitHub()
    if args.mode == "prepare":
        prepare(api, args.path)
    else:
        print(json.dumps(publish(api, args.path)))


if __name__ == "__main__":
    main()
