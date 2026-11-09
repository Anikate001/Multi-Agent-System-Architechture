"""API contract tests: the routes the Streamlit frontend calls must exist, and task
status must map to the values the frontend understands. Uses a fake orchestrator,
so no API keys, Postgres or Redis are needed."""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


from api import routes  # noqa: E402

REPORT = {"title": "T", "abstract": "A", "sections": [{"title": "S", "content": "C", "citations": []}],
          "bibliography": [{"url": "https://x.org", "title": "X", "snippet": "s"}], "total_citations": 0,
          "quality_score": 8}


class FakeGraph:
    def __init__(self):
        self.states = {}

    def get_state(self, config):
        tid = config["configurable"]["thread_id"]
        values, nxt = self.states.get(tid, ({}, ()))
        return SimpleNamespace(values=values, next=nxt)


class FakeOrchestrator:
    def __init__(self):
        self.graph = FakeGraph()
        self.approved = []

    async def run(self, task, task_id, callback=None):
        self.graph.states[task_id] = ({"draft_report": REPORT, "current_agent": "CRITIC"}, ())
        return SimpleNamespace(model_dump=lambda **kw: REPORT)

    async def get_state(self, task_id):
        return {}

    async def approve_task(self, task_id):
        self.approved.append(task_id)

    async def reject_task(self, task_id, feedback):
        pass


class FakeDB:
    async def save_task(self, *a, **k):
        pass


@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(routes.router, prefix="/api/v1")
    app.state.orchestrator = FakeOrchestrator()
    app.state.db = FakeDB()
    app.state.tasks = {}
    app.state.settings = SimpleNamespace(max_runs_per_day=0, max_concurrent_runs=0)
    return TestClient(app), app


def test_daily_run_limit_returns_429(client):
    c, app = client
    app.state.settings.max_runs_per_day = 1
    assert c.post("/api/v1/research", json={"query": "first question here"}).status_code == 200
    r = c.post("/api/v1/research", json={"query": "second question here"})
    assert r.status_code == 429 and "per day" in r.json()["detail"]


def test_concurrent_run_limit_returns_429(client):
    c, app = client
    app.state.settings.max_concurrent_runs = 1
    app.state.tasks["busy"] = {"query": "q", "started_at": 0, "failed": False}
    r = c.post("/api/v1/research", json={"query": "another question"})
    assert r.status_code == 429


def test_full_lifecycle_on_frontend_paths(client):
    c, app = client
    r = c.post("/api/v1/research", json={"query": "What is retrieval-augmented generation?"})
    assert r.status_code == 200
    tid = r.json()["task_id"]
    # Background task has run (TestClient runs background tasks before returning)
    s = c.get(f"/api/v1/research/{tid}/status").json()
    assert s["status"] == "completed"
    assert s["progress_pct"] == 100.0
    assert c.get(f"/api/v1/research/{tid}/report").json()["title"] == "T"
    md = c.get(f"/api/v1/research/{tid}/export/markdown").text
    assert md.startswith("# T") and "[X](https://x.org)" in md
    m = c.get("/api/v1/metrics").json()
    assert m["total_tasks"] == 1 and m["failed_tasks"] == 0


def test_needs_approval_and_approve(client):
    c, app = client
    tid = "t-approval"
    app.state.tasks[tid] = {"query": "q", "started_at": 0, "failed": False}
    app.state.orchestrator.graph.states[tid] = ({"draft_report": REPORT}, ("human_review",))
    assert c.get(f"/api/v1/research/{tid}/status").json()["status"] == "needs_approval"
    assert c.post(f"/api/v1/research/{tid}/approve").status_code == 200
    assert app.state.orchestrator.approved == [tid]


def test_approve_rejected_when_not_waiting(client):
    c, app = client
    tid = "t-done"
    app.state.tasks[tid] = {"query": "q", "started_at": 0, "failed": False}
    app.state.orchestrator.graph.states[tid] = ({"draft_report": REPORT}, ())
    assert c.post(f"/api/v1/research/{tid}/approve").status_code == 409


def test_failed_task_reports_failed(client):
    c, app = client
    tid = "t-fail"
    app.state.tasks[tid] = {"query": "q", "started_at": 0, "failed": True, "error": "boom"}
    assert c.get(f"/api/v1/research/{tid}/status").json()["status"] == "failed"


def test_unknown_task_is_404(client):
    c, _ = client
    assert c.get("/api/v1/research/nope/status").status_code == 404
