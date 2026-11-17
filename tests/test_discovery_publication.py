"""Exercise publication with a fake GitHub API; no remote writes are performed."""

import base64
import copy
import importlib.util
from io import BytesIO
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mia_capital_intelligence.discovery_catalog import observe, read_catalog, serialize_catalog
from mia_capital_intelligence.discovery_sources import KEYWORD_SEARCH, QUARTERLY, ReportLink, inspect_pdf

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("discovery_publisher", ROOT / "scripts/publish_report_discovery.py")
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


@pytest.fixture
def bundle(tmp_path, synthetic_pdf, monkeypatch):
    (tmp_path / "data/discovery").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    base = {"schema_version": 1, "documents": [], "locations": [], "events": []}
    (tmp_path / "data/discovery/catalog.json").write_text(serialize_catalog(base))
    (tmp_path / "docs/DATA_UPDATES.md").write_text("# Published source inventory\n")
    link = ReportLink(QUARTERLY, "Infrastructure 241354", "https://www.miamidade.gov/report.pdf", KEYWORD_SEARCH, "PDF")
    identity = inspect_pdf(synthetic_pdf("Infrastructure 241354 Quarterly Report: 4/01/2026-06/30/2026"), link)
    catalog = copy.deepcopy(base)
    observe(catalog, link, identity, {}, datetime(2026, 11, 17, tzinfo=timezone.utc))
    folder = tmp_path / "tmp/bundle"
    folder.mkdir(parents=True)
    (folder / "catalog.json").write_text(serialize_catalog(catalog))
    (folder / "report.json").write_text(json.dumps({"changed": True, "new_events": 1, "status": "ok"}))
    monkeypatch.setattr(publisher, "ROOT", tmp_path)
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    return folder, catalog


class FakeGitHub:
    repository = "sample/project"

    def __init__(self, *, prior=None, state=None, branch=None):
        self.prior, self.branch = prior, branch
        self.latest = {"state": state, "number": 12, "html_url": "https://github.com/sample/project/pull/12"} if state else None
        self.calls = []
        self.files = {}
        self.commits = 0

    def history(self):
        return ({"object": {"sha": self.branch}} if self.branch else None, self.latest, self.prior)

    def call(self, method, path, body=None, **kwargs):
        self.calls.append((method, path, body))
        if method == "GET":
            if path == "":
                return {"default_branch": "main"}
            if path == "git/ref/heads/main":
                return {"object": {"sha": "main-sha"}}
            if path == "git/ref/heads/automation/report-discovery":
                return {"object": {"sha": self.branch}} if self.branch else None
            if path.startswith("git/commits/"):
                return {"tree": {"sha": "main-tree"}}
        if path == "git/trees":
            self.files = {row["path"]: row["content"] for row in body["tree"]}
            return {"sha": "new-tree"}
        if path == "git/commits":
            self.commits += 1
            return {"sha": f"new-commit-{self.commits}"}
        if path in {"git/refs", "git/refs/heads/automation/report-discovery"}:
            self.branch = body["sha"]
            self.prior = json.loads(self.files["data/discovery/catalog.json"])
            return {}
        if path == "pulls":
            self.latest = {"state": "open", "number": 12, "html_url": "https://github.com/sample/project/pull/12"}
            return self.latest
        if path == "pulls/12":
            return self.latest
        raise AssertionError((method, path))


def test_new_proposal_limits_paths_preserves_parents_and_links_real_pr(bundle):
    folder, catalog = bundle
    api = FakeGitHub()
    result = publisher.publish(api, folder)
    assert result["pull_request"] == "https://github.com/sample/project/pull/12"
    assert api.commits == 2
    assert set(api.files) == {"data/discovery/catalog.json", "docs/DATA_UPDATES.md"}
    assert api.prior["events"][0]["pull_request_url"] == result["pull_request"]
    assert result["pull_request"] in api.files["docs/DATA_UPDATES.md"]
    assert all(body.get("force") is False for method, path, body in api.calls if method == "PATCH" and path.startswith("git/refs"))
    assert not any(path == "git/refs/heads/main" for _, path, _ in api.calls)
    commits = [body for method, path, body in api.calls if path == "git/commits"]
    assert commits[0]["parents"] == ["main-sha"]
    assert commits[1]["parents"] == ["new-commit-1", "main-sha"]


def test_open_proposal_is_updated_in_place(bundle):
    folder, catalog = bundle
    api = FakeGitHub(state="open", branch="prior-head")
    publisher.publish(api, folder)
    assert not any(method == "POST" and path == "pulls" for method, path, _ in api.calls)
    assert any(method == "PATCH" and path == "pulls/12" for method, path, _ in api.calls)
    assert api.commits == 1
    assert next(body for _, path, body in api.calls if path == "git/commits")["parents"] == ["prior-head", "main-sha"]


def test_unchanged_closed_or_deleted_proposal_is_not_reopened(bundle):
    folder, catalog = bundle
    for branch in (None, "prior-head"):
        api = FakeGitHub(prior=catalog, state="closed", branch=branch)
        assert publisher.publish(api, folder)["status"] == "unchanged_closed_proposal"
        assert api.calls == []


def test_duplicate_scan_after_another_publication_has_no_write(bundle):
    folder, catalog = bundle
    catalog["events"][0]["pull_request_url"] = "https://github.com/sample/project/pull/12"
    (folder / "catalog.json").write_text(serialize_catalog(catalog))
    api = FakeGitHub(prior=catalog, state="open", branch="prior-head")
    assert publisher.publish(api, folder)["status"] == "already_published"
    assert api.calls == []


def test_pr_link_write_is_retried_after_an_interrupted_publication(bundle):
    folder, catalog = bundle
    (folder / "report.json").write_text(json.dumps({"changed": False, "new_events": 0, "status": "ok"}))
    api = FakeGitHub(prior=catalog, state="open", branch="prior-head")
    assert publisher.publish(api, folder)["status"] == "proposed"
    assert api.prior["events"][0]["pull_request_url"] == "https://github.com/sample/project/pull/12"


def test_moved_main_stops_stale_catalog_publication(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "outdated-main")
    api = FakeGitHub()
    with pytest.raises(ValueError, match="Default branch changed"):
        publisher.commit_files(api, {"data/discovery/catalog.json": "{}", "docs/DATA_UPDATES.md": "# Log"}, None)
    assert not any(method in {"POST", "PATCH"} for method, _, _ in api.calls)


def test_candidate_cannot_promote_itself_to_published_data(bundle):
    folder, catalog = bundle
    catalog["documents"][0]["dataset_status"] = "included"
    (folder / "catalog.json").write_text(serialize_catalog(catalog))
    api = FakeGitHub()
    with pytest.raises(ValueError, match="cannot add or remove published"):
        publisher.publish(api, folder)
    assert api.calls == []


def test_arbitrary_paths_cannot_be_committed():
    api = FakeGitHub()
    with pytest.raises(ValueError, match="only"):
        publisher.commit_files(api, {"streamlit_app.py": "unexpected"}, None)
    assert api.calls == []


def test_branch_race_stops_before_ref_update():
    api = FakeGitHub(branch="concurrently-updated")
    with pytest.raises(ValueError, match="changed during publication"):
        publisher.commit_files(api, {"data/discovery/catalog.json": "{}", "docs/DATA_UPDATES.md": "# Log"}, "expected-head")
    assert not any(method == "PATCH" and path.startswith("git/refs") for method, path, _ in api.calls)


def test_closed_pr_history_is_loaded_by_commit_after_branch_deletion(bundle):
    folder, catalog = bundle
    api = object.__new__(publisher.GitHub)
    api.repository = "sample/project"
    requested = []
    def call(method, path, body=None, **kwargs):
        requested.append(path)
        if path.startswith("git/ref/"):
            return None
        if path.startswith("pulls?"):
            return [{"head": {"sha": "retained-closed-head"}, "state": "closed"}]
        if path.startswith("contents/"):
            return {"content": base64.b64encode(serialize_catalog(catalog).encode()).decode()}
        raise AssertionError(path)
    api.call = call
    _, _, previous = api.history()
    assert previous == catalog
    assert any("ref=retained-closed-head" in path for path in requested)


def test_repository_api_root_has_no_trailing_slash(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "sample/project")
    monkeypatch.setenv("GH_TOKEN", "synthetic-test-token")
    urls = []
    def open_response(request, **kwargs):
        urls.append(request.full_url)
        return BytesIO(b'{"default_branch":"main"}')
    monkeypatch.setattr(publisher, "urlopen", open_response)
    assert publisher.GitHub().call("GET", "") == {"default_branch": "main"}
    assert urls == ["https://api.github.com/repos/sample/project"]


def test_api_mutations_use_json_body_and_content_type(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "sample/project")
    monkeypatch.setenv("GH_TOKEN", "synthetic-test-token")
    requests = []
    def open_response(request, **kwargs):
        requests.append(request)
        return BytesIO(b'{"sha":"new-tree"}')
    monkeypatch.setattr(publisher, "urlopen", open_response)
    publisher.GitHub().call("POST", "git/trees", {"tree": []})
    assert requests[0].get_header("Content-type") == "application/json"
    assert json.loads(requests[0].data) == {"tree": []}
