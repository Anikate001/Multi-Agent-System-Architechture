#!/bin/sh
# Starts Redis, the FastAPI backend (internal only) and the Streamlit UI on the Space's port.
set -e
cd "$(dirname "$0")/../.."

redis-server --daemonize yes --save "" --appendonly no --maxmemory 128mb --maxmemory-policy allkeys-lru --dir /tmp

(cd backend && uvicorn main:app --host 127.0.0.1 --port 8000 --log-level warning) &

# Wait for the backend before serving the UI
for i in $(seq 1 60); do
  python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" 2>/dev/null && break
  sleep 1
done

cd frontend
exec streamlit run app.py --server.port "${PORT:-7860}" --server.address 0.0.0.0 --server.headless true \
  --browser.gatherUsageStats false
