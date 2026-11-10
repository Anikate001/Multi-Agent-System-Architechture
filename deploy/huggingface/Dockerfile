# NEXUS as one Hugging Face Docker Space: Redis + FastAPI backend + Streamlit UI in a single container.
# The Space only holds this file and README.md; the code is cloned from GitHub at build time,
# so a "Factory rebuild" of the Space picks up the latest commit on main.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends redis-server git \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face runs Spaces as user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user

ARG NEXUS_REPO=https://github.com/Anikate001/Multi-Agent-System-Architechture.git
ARG NEXUS_REF=main
# Busts the build cache whenever the branch moves, so rebuilds never reuse stale code
ADD --chown=user https://api.github.com/repos/Anikate001/Multi-Agent-System-Architechture/commits/${NEXUS_REF} /tmp/nexus-version.json
RUN git clone --depth 1 --branch ${NEXUS_REF} ${NEXUS_REPO} app

RUN pip install --no-cache-dir --user -r app/backend/requirements.txt -r app/frontend/requirements.txt aiosqlite

# Demo settings. GEMINI_API_KEY and TAVILY_API_KEY come from the Space's secrets.
ENV DATABASE_URL=sqlite+aiosqlite:////tmp/nexus.db \
    REDIS_URL=redis://127.0.0.1:6379/0 \
    NEXUS_BACKEND_URL=http://127.0.0.1:8000 \
    MODEL_NAME=gemini-3.5-flash-lite \
    MAX_RUNS_PER_DAY=25 \
    MAX_CONCURRENT_RUNS=1 \
    PYTHONUNBUFFERED=1

EXPOSE 7860
CMD ["sh", "app/deploy/huggingface/start.sh"]
