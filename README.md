# 🤖 Multi-Agent System Architecture

> A production-level multi-agent AI system built with **LangGraph** + **GPT-4o**, featuring 5 specialized agents working together through an intelligent workflow graph.

---

## 🏗️ Architecture

```
                 ┌──────────────┐
                 │   User Input │
                 └──────┬───────┘
                        ↓
                ┌──────────────┐
                │   Planner    │  ← Analyzes task, creates plan, decides route
                └──────┬───────┘
                       ↓
          ┌────────────┴────────────┐
          ↓                         ↓
   ┌──────────────┐         ┌──────────────┐
   │  Researcher  │         │    Coder     │  ← Specialist agents
   └──────┬───────┘         └──────┬───────┘
          └────────────┬───────────┘
                       ↓
                ┌──────────────┐
                │   Reviewer   │  ← Quality control (can loop back!)
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │  Aggregator  │  ← Final output assembly
                └──────────────┘
                       ↓
                    Output
```

### Agent Roles

| Agent | Role | Key Feature |
|-------|------|-------------|
| 🧠 **Planner** | Analyzes tasks, creates execution plans | Intelligent routing (research/code/both) |
| 🔍 **Researcher** | Web search & information gathering | Tavily API + DuckDuckGo fallback |
| 💻 **Coder** | Code generation & revision | Context-aware, handles revision feedback |
| 🔎 **Reviewer** | Quality control & critique | Feedback loop with max revision guard |
| 📦 **Aggregator** | Final output assembly | Synthesizes all agent work |

### Key Features

- ✅ **Conditional Routing** — Planner decides which agents are needed
- ✅ **Feedback Loop** — Reviewer can send work back for revision (max 2x)
- ✅ **State Management** — Shared memory with smart message reducers
- ✅ **Tool Integration** — Web search (Tavily/DDG) + sandboxed code execution
- ✅ **Memory Persistence** — MemorySaver checkpointer for session continuity
- ✅ **Dual Interface** — CLI + Streamlit UI

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd Multi-Agent-Sytem-Architechture
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Run (CLI)

```bash
# Single task
python main.py "Build a Python function to calculate fibonacci numbers"

# Interactive mode
python main.py
```

### 4. Run (Streamlit UI)

```bash
streamlit run app.py
```

---

## 🧱 Project Structure

```
├── .env.example          # API key template
├── requirements.txt      # Dependencies
├── config.py             # Configuration & LLM setup
├── state.py              # AgentState schema (shared memory)
├── tools.py              # Web search + code execution tools
├── agents/
│   ├── __init__.py
│   ├── planner.py        # Task analysis & routing
│   ├── researcher.py     # Web search & synthesis
│   ├── coder.py          # Code generation & revision
│   ├── reviewer.py       # Quality review & feedback loop
│   └── aggregator.py     # Final output assembly
├── graph.py              # LangGraph workflow definition
├── main.py               # CLI entry point
├── app.py                # Streamlit UI
└── README.md
```

---

## ⚙️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Orchestration** | LangGraph (StateGraph) |
| **LLM** | OpenAI GPT-4o via langchain-openai |
| **State** | TypedDict + `add_messages` reducer |
| **Search** | Tavily API (primary) + DuckDuckGo (fallback) |
| **UI** | Streamlit |
| **Memory** | MemorySaver (in-memory checkpointer) |

---

## 🔄 How It Works

1. **User submits a task** (CLI or Streamlit)
2. **Planner** analyzes it → creates plan → decides route:
   - `researcher` → task needs information gathering
   - `coder` → task needs code generation
   - `researcher_then_coder` → needs both, in order
   - `direct_review` → simple enough for direct answer
3. **Specialist agents** execute their roles
4. **Reviewer** evaluates the work:
   - `PASS` → sends to Aggregator
   - `NEEDS_REVISION` → loops back (max 2 times)
5. **Aggregator** synthesizes everything into a polished response

---

## 🛠️ Adding New Agents

1. Create `agents/your_agent.py` with a function matching this signature:
```python
def your_agent(state: dict) -> dict:
    # Process state
    return {"messages": [...], "your_key": "output"}
```

2. Add the state key to `state.py`
3. Register the node in `graph.py`:
```python
graph.add_node("your_agent", your_agent)
```
4. Wire edges in `graph.py`

---

## 📄 License

MIT License — Use freely for learning and building.
