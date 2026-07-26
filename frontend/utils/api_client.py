"""
Nexus Research Platform — API Client
Handles all communication with the FastAPI backend.
"""

import os
import requests
from typing import Optional
from dataclasses import dataclass


@dataclass
class APIError:
    """Structured API error for user-friendly display."""
    status_code: int
    message: str
    detail: str


class NexusAPIClient:
    """
    Client for the Nexus multi-agent research backend.
    Wraps every endpoint with retry logic and friendly error surfaces.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (
            base_url
            or os.getenv("NEXUS_BACKEND_URL", "http://backend:8000")
        ).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self.timeout = 30

    # ── helpers ──────────────────────────────────────────────────────
    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, resp: requests.Response) -> dict:
        """Parse response; raise friendly errors on failure."""
        try:
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError:
            detail = ""
            try:
                body = resp.json()
                detail = body.get("detail", body.get("message", str(body)))
            except Exception:
                detail = resp.text[:300]
            raise RuntimeError(
                self._friendly_error(resp.status_code, detail)
            )
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "🔌 Unable to reach the Nexus backend. "
                "Please verify the service is running and your network is connected."
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(
                "⏳ The request timed out. The backend may be under heavy load — "
                "please try again in a moment."
            )
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"⚠️ Unexpected request error: {exc}")

    @staticmethod
    def _friendly_error(status_code: int, detail: str) -> str:
        messages = {
            400: "🚫 Bad request — please check your input and try again.",
            401: "🔒 Authentication required. Please log in.",
            403: "🚫 You don't have permission for this action.",
            404: "🔍 Resource not found. It may have been deleted or the ID is invalid.",
            409: "⚠️ Conflict — another operation is in progress for this task.",
            422: "📋 Validation error — please review the form fields.",
            429: "🐢 Too many requests. Please wait a moment before retrying.",
            500: "💥 Internal server error. The team has been notified.",
            502: "🌐 Bad gateway — the backend is temporarily unreachable.",
            503: "🔧 Service unavailable — maintenance may be in progress.",
        }
        base = messages.get(status_code, f"❌ Error {status_code}")
        if detail:
            return f"{base}\n\nDetails: {detail}"
        return base

    # ── research lifecycle ───────────────────────────────────────────
    def start_research(
        self,
        query: str,
        depth: str = "standard",
        max_sources: int = 20,
        require_approval: bool = False,
        include_code_analysis: bool = False,
    ) -> dict:
        """Launch a new multi-agent research task."""
        payload = {
            "query": query,
            "depth": depth,
            "max_sources": max_sources,
            "require_approval": require_approval,
            "include_code_analysis": include_code_analysis,
        }
        resp = self.session.post(
            self._url("/api/v1/research"),
            json=payload,
            timeout=self.timeout,
        )
        return self._handle_response(resp)

    def get_task_status(self, task_id: str) -> dict:
        """Poll the current status of a research task."""
        resp = self.session.get(
            self._url(f"/api/v1/research/{task_id}/status"),
            timeout=self.timeout,
        )
        return self._handle_response(resp)

    def approve_task(self, task_id: str) -> dict:
        """Approve the report produced by the research pipeline."""
        resp = self.session.post(
            self._url(f"/api/v1/research/{task_id}/approve"),
            timeout=self.timeout,
        )
        return self._handle_response(resp)

    def reject_task(self, task_id: str, feedback: str = "") -> dict:
        """Reject the report and optionally supply revision feedback."""
        payload = {"feedback": feedback}
        resp = self.session.post(
            self._url(f"/api/v1/research/{task_id}/reject"),
            json=payload,
            timeout=self.timeout,
        )
        return self._handle_response(resp)

    def get_report(self, task_id: str) -> dict:
        """Retrieve the final (or latest draft) report."""
        resp = self.session.get(
            self._url(f"/api/v1/research/{task_id}/report"),
            timeout=self.timeout,
        )
        return self._handle_response(resp)

    def export_markdown(self, task_id: str) -> str:
        """Download the report as raw Markdown text."""
        resp = self.session.get(
            self._url(f"/api/v1/research/{task_id}/export/markdown"),
            timeout=self.timeout,
        )
        try:
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                data = resp.json()
                return data.get("markdown", data.get("content", str(data)))
            return resp.text
        except requests.exceptions.HTTPError:
            raise RuntimeError(
                self._friendly_error(resp.status_code, resp.text[:200])
            )

    # ── observability ────────────────────────────────────────────────
    def get_health(self) -> dict:
        """Check backend health status."""
        try:
            resp = self.session.get(
                self._url("/health"),
                timeout=5,
            )
            return self._handle_response(resp)
        except RuntimeError:
            return {"status": "unreachable", "latency_ms": None}

    def get_metrics(self) -> dict:
        """Fetch global platform metrics."""
        try:
            resp = self.session.get(
                self._url("/api/v1/metrics"),
                timeout=10,
            )
            return self._handle_response(resp)
        except RuntimeError:
            return {
                "total_tasks": 0,
                "tokens_used": 0,
                "avg_latency_ms": 0,
                "agents": {},
            }

    # ── websocket url helper ─────────────────────────────────────────
    def ws_url(self, task_id: str) -> str:
        """Return the WebSocket URL for live task streaming."""
        ws_base = self.base_url.replace("http://", "ws://").replace(
            "https://", "wss://"
        )
        return f"{ws_base}/ws/research/{task_id}"
