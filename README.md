<div align="center">

# 🧠 NEXUS

### A multi-agent research platform: five LangGraph agents plan, research, analyse, write and critique a cited report, with a human in the loop when it matters.

<p>
  <img src="https://img.shields.io/badge/LangGraph-state%20machine-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangGraph">
  <img src="https://img.shields.io/badge/FastAPI-async-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Gemini-2.0%20Flash-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini 2.0 Flash">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose">
</p>
<p>
  <a href="https://github.com/Anikate001/Multi-Agent-System-Architechture/actions/workflows/tests.yml"><img src="https://github.com/Anikate001/Multi-Agent-System-Architechture/actions/workflows/tests.yml/badge.svg" alt="tests"></a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square" alt="MIT">
</p>

[Architecture](#-architecture) · [Agents](#-the-agents) · [Quick start](#-quick-start) · [API](#-api) · [Benchmark](#-benchmark)

</div>

---

## ✨ Highlights

- **A real state machine, not a free-running agent loop.** LangGraph makes every transition explicit: plan → research → analyse → write → review, with a bounded revision loop.
- **Self-critique.** A Critic agent scores each draft from 1 to 10 and sends anything below 7 back to the Writer, up to 3 times.
- **Human-in-the-loop.** With approval enabled, the graph genuinely pauses before completion (`interrupt_before`) until a person approves or rejects with feedback.
- **Cited by construction.** The Researcher pulls sources through Tavily search, and every claim in the report links to a source.
- **Production plumbing.** Async FastAPI with WebSocket progress streaming, Pydantic-validated agent outputs, PostgreSQL persistence, Redis-cached search, a health check, Docker Compose, and API tests in GitHub Actions.

## 🏗️ Architecture

```mermaid
flowchart LR
    UI["🖥️ Streamlit UI"] <-- "REST + WebSockets" --> API["⚡ FastAPI"]
    API --> ORCH["🧩 LangGraph orchestrator"]
    ORCH <--> PG[("PostgreSQL<br/>tasks + reports")]
    ORCH <--> RD[("Redis<br/>state + search cache")]
    ORCH --> AG["🤖 5 agents"]
    AG <--> LLM["Gemini 2.0 Flash"]
    AG <--> WEB["Tavily web search"]
```

### Workflow

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Planner
    Planner --> Researcher: sub-tasks
    Researcher --> Analyst: findings + sources
    Analyst --> Writer: synthesis
    Writer --> Critic: draft
    Critic --> Writer: score < 7 (max 3 revisions)
    Critic --> HumanReview: approved, approval required
    Critic --> [*]: approved
    HumanReview --> Writer: rejected with feedback
    HumanReview --> [*]: approved
```

More diagrams: [`docs/architecture.md`](docs/architecture.md).

## 🤖 The agents

| Agent | Job | Output |
|---|---|---|
| **Planner** | Breaks the question into a structured research plan | Sub-tasks with dependencies |
| **Researcher** | Searches the web (Tavily, cached in Redis) and extracts facts | Findings with sources |
| **Analyst** | Synthesises findings, spots patterns and contradictions | Analytical narrative |
| **Writer** | Writes the report with inline citations | Draft report |
| **Critic** | Reviews for unsupported claims, coherence and citation quality | 1-10 score, approve or revise |

All agent outputs are Pydantic models, LLM calls retry with `tenacity`, and a context manager summarises older
state to stay inside the token budget.

## 🚀 Quick start

**Prerequisites:** Docker, a [Gemini API key](https://aistudio.google.com/apikey) and a [Tavily API key](https://tavily.com).

```bash
git clone https://github.com/Anikate001/Multi-Agent-System-Architechture.git
cd Multi-Agent-System-Architechture/infra
cp .env.example .env          # add GEMINI_API_KEY and TAVILY_API_KEY
docker compose up --build     # UI: http://localhost:8501 · API docs: http://localhost:8000/docs
```

<details>
<summary><b>Run the backend without Docker</b></summary>

```bash
docker compose -f infra/docker-compose.yml up -d db redis   # Postgres + Redis only
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY=... TAVILY_API_KEY=...
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/nexus
export REDIS_URL=redis://localhost:6379/0
uvicorn main:app --reload
```

</details>

## 🔌 API

Served under both `/api` and `/api/v1`.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/research` | Start a research task (`query`, `depth`, `max_sources`, `require_approval`) |
| `GET` | `/research/{id}/status` | `running` · `needs_approval` · `completed` · `failed`, with progress and agent actions |
| `GET` | `/research/{id}/report` | Latest report as JSON |
| `GET` | `/research/{id}/export/markdown` | Report as Markdown |
| `POST` | `/research/{id}/approve` | Approve a paused report |
| `POST` | `/research/{id}/reject` | Reject with `{"feedback": "..."}` to trigger a revision |
| `GET` | `/metrics` | Task counts, tokens, average latency |
| `GET` | `/health` | Database and Redis health |
| `WS` | `/ws/research/{id}` | Live progress events |

## 📏 Benchmark

[`backend/benchmarks/run_benchmark.py`](backend/benchmarks/run_benchmark.py) runs the full workflow on 10 fixed
research questions and reports success rate, p50/p95 latency, time per agent, mean Critic score, first-draft
approval rate, revision loops, citations per report and the Redis cache speed-up.

```bash
cd backend && python -m benchmarks.run_benchmark --limit 3   # quick smoke test
```

## 🧪 Tests

```bash
cd backend && python -m pytest tests -q
```

Includes API contract tests that run the full request lifecycle against a fake orchestrator, so they need no API
keys, Postgres or Redis. They run on every push in GitHub Actions.

## 📁 Project structure

```
├── backend/
│   ├── agents/          # Planner, Researcher, Analyst, Writer, Critic
│   ├── api/             # REST routes and WebSocket manager
│   ├── orchestration/   # LangGraph graph, nodes and state
│   ├── memory/          # Context summarisation, state persistence
│   ├── services/        # LLM, PostgreSQL and Redis services
│   ├── tools/           # Web search, PDF parsing, citation extraction
│   ├── schemas/         # Pydantic models
│   ├── benchmarks/      # End-to-end benchmark
│   └── tests/           # Pytest suite
├── frontend/            # Streamlit dashboard
├── infra/               # Docker Compose stack
├── docs/                # Architecture diagrams and notes
└── legacy/              # First single-process prototype
```

<details>
<summary><b>💬 Design FAQ</b></summary>

**Why LangGraph instead of a classic agent executor?**
An executor decides its next step at runtime, which is hard to control. A LangGraph state machine makes control flow
explicit, so loops like critique-and-revise and pauses for human review are predictable and testable.

**How does state move between agents?**
Through a typed `ResearchState` with reducers: lists such as `agent_actions` append, while fields such as
`current_agent` overwrite. Progress is also written to Redis and PostgreSQL after every step.

**How are long research tasks kept inside the context window?**
The Researcher passes structured findings (summaries and key points) rather than raw pages, and a context manager
summarises older messages when the token budget runs low.

**What if the model returns malformed JSON?**
Outputs are parsed into Pydantic models, and calls are wrapped in `tenacity` retries.

</details>

## 📝 License

MIT
