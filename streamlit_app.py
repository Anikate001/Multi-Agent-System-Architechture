"""NEXUS on Streamlit Community Cloud: the whole platform in one process.

Streamlit Cloud runs a single Streamlit app with no Redis or Postgres, so this entry point
starts the FastAPI backend in a background thread (SQLite + an in-memory Redis) and then
runs the normal Streamlit frontend against it on localhost.

Secrets (Streamlit Cloud -> App settings -> Secrets, which become environment variables):
    GEMINI_API_KEY = "..."
    TAVILY_API_KEY = "..."
"""
import os
import sys
import threading
import time
import urllib.request
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
BACKEND_PORT = 8000

# Demo defaults; anything set in secrets/env wins.
for key, value in {
    "DATABASE_URL": "sqlite+aiosqlite:////tmp/nexus.db",
    "REDIS_URL": "memory://",
    "NEXUS_BACKEND_URL": f"http://127.0.0.1:{BACKEND_PORT}",
    "MODEL_NAME": "gemini-3.5-flash-lite",
    "MAX_RUNS_PER_DAY": "25",
    "MAX_CONCURRENT_RUNS": "1",
}.items():
    os.environ.setdefault(key, value)

# Streamlit Cloud exposes secrets as env vars only for top-level keys; copy them explicitly too.
for key in ("GEMINI_API_KEY", "TAVILY_API_KEY"):
    try:
        if key not in os.environ and key in st.secrets:
            os.environ[key] = str(st.secrets[key])
    except Exception:
        pass

for sub in ("backend", "frontend"):
    path = str(ROOT / sub)
    if path not in sys.path:
        sys.path.insert(0, path)


def _backend_healthy() -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{BACKEND_PORT}/health", timeout=2)
        return True
    except Exception:
        return False


@st.cache_resource(show_spinner="Starting the NEXUS backend...")
def start_backend() -> bool:
    """Start uvicorn once per server process and wait until /health answers."""
    if _backend_healthy():
        return True
    import uvicorn

    os.chdir(ROOT / "backend")  # the backend resolves its .env and modules from here
    config = uvicorn.Config("main:app", host="127.0.0.1", port=BACKEND_PORT, log_level="warning")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True, name="nexus-backend").start()
    for _ in range(60):
        if _backend_healthy():
            return True
        time.sleep(0.5)
    return False


if not (os.environ.get("GEMINI_API_KEY") and os.environ.get("TAVILY_API_KEY")):
    st.error("GEMINI_API_KEY and TAVILY_API_KEY are not set. Add them in the app's Secrets.")
    st.stop()

if not start_backend():
    st.error("The NEXUS backend did not start. Check the app logs.")
    st.stop()

os.chdir(ROOT / "frontend")
with open(ROOT / "frontend" / "app.py", encoding="utf-8") as f:
    exec(
        compile(f.read(), str(ROOT / "frontend" / "app.py"), "exec"),
        {"__name__": "__main__", "__file__": str(ROOT / "frontend" / "app.py")},
    )
