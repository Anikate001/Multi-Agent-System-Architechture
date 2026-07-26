"""
Multi-Agent System — Streamlit UI

A premium chat-style interface with:
- Real-time agent status indicators
- Expandable agent thought process
- Task history sidebar
- Beautiful dark theme

Run with:
    streamlit run app.py
"""

import uuid
import time
import streamlit as st
from config import validate_config, OPENAI_API_KEY
from graph import get_app


# ═══════════════════════════════════════════════════════════════════════
#  PAGE CONFIG & STYLING
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Multi-Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium Dark Theme CSS ──────────────────────────────────────────
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    .main-header h1 {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        font-size: 1rem;
        opacity: 0.9;
        font-weight: 300;
    }

    /* Agent Status Cards */
    .agent-card {
        padding: 1rem 1.2rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
        border-left: 4px solid;
        transition: all 0.3s ease;
    }
    .agent-active {
        background: rgba(102, 126, 234, 0.1);
        border-left-color: #667eea;
        animation: pulse 2s infinite;
    }
    .agent-done {
        background: rgba(72, 187, 120, 0.1);
        border-left-color: #48bb78;
    }
    .agent-waiting {
        background: rgba(160, 174, 192, 0.05);
        border-left-color: #a0aec0;
        opacity: 0.6;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Output Box */
    .output-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #e2e8f0;
        padding: 2rem;
        border-radius: 16px;
        font-family: 'Inter', monospace;
        font-size: 0.95rem;
        line-height: 1.7;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }

    /* Stats Row */
    .stat-card {
        background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.15);
    }
    .stat-card h3 {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-card p {
        font-size: 0.8rem;
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Sidebar styling */
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(102, 126, 234, 0.3);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
#  SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════════════

if "task_history" not in st.session_state:
    st.session_state.task_history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False


# ═══════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ Configuration</div>', unsafe_allow_html=True)

    # API Key status
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-your"):
        st.success("✅ OpenAI API Key loaded", icon="🔑")
    else:
        st.error("❌ OpenAI API Key missing", icon="🔑")
        st.info("Add your key to `.env` file")

    st.divider()

    # Architecture diagram
    st.markdown('<div class="sidebar-title">🏗️ Agent Architecture</div>', unsafe_allow_html=True)
    st.code("""
    User Input
       ↓
    ┌──────────┐
    │ Planner  │
    └────┬─────┘
         ↓
    ┌────┴────┐
    ↓         ↓
Research   Coder
    ↓         ↓
    └────┬────┘
         ↓
    ┌──────────┐
    │ Reviewer │◄──┐
    └────┬─────┘   │
         ↓     (retry)
    ┌──────────┐   │
    │Aggregator│───┘
    └──────────┘
         ↓
      Output
    """, language=None)

    st.divider()

    # Task History
    st.markdown('<div class="sidebar-title">📜 Task History</div>', unsafe_allow_html=True)
    if st.session_state.task_history:
        for i, entry in enumerate(reversed(st.session_state.task_history[-10:])):
            with st.expander(f"#{len(st.session_state.task_history) - i}: {entry['task'][:40]}...", expanded=False):
                st.caption(f"⏱️ {entry['elapsed']:.1f}s | 🔄 {entry['revisions']} revisions")
                st.caption(f"🛤️ {entry['path']}")
    else:
        st.caption("No tasks yet. Submit one above!")


# ═══════════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════════

# ── Header ──────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🤖 Multi-Agent System</h1>
    <p>Powered by LangGraph + GPT-4o — Planner, Researcher, Coder, Reviewer & Aggregator working together</p>
</div>
""", unsafe_allow_html=True)

# ── Task Input ──────────────────────────────────────────────────────
col1, col2 = st.columns([5, 1])

with col1:
    task_input = st.text_area(
        "🎯 What would you like the agent team to work on?",
        placeholder="Example: Build a Python web scraper that extracts product prices from Amazon...",
        height=100,
        key="task_input",
    )

with col2:
    st.write("")  # Spacing
    st.write("")
    run_button = st.button("🚀 Run", type="primary", use_container_width=True, disabled=st.session_state.is_running)

# ── Example Tasks ───────────────────────────────────────────────────
st.markdown("**Quick examples:**")
example_cols = st.columns(4)

examples = [
    "Build a Python calculator with GUI",
    "Research latest AI agent frameworks",
    "Create a REST API with FastAPI",
    "Explain how transformers work",
]

for i, (col, example) in enumerate(zip(example_cols, examples)):
    with col:
        if st.button(example, key=f"example_{i}", use_container_width=True):
            st.session_state.task_input = example
            st.rerun()

st.divider()


# ═══════════════════════════════════════════════════════════════════════
#  EXECUTION
# ═══════════════════════════════════════════════════════════════════════

if run_button and task_input.strip():
    if not validate_config():
        st.error("❌ Please configure your OpenAI API key in `.env`")
        st.stop()

    st.session_state.is_running = True

    # ── Agent status display ────────────────────────────────────────
    status_cols = st.columns(5)
    agent_names = ["🧠 Planner", "🔍 Researcher", "💻 Coder", "🔎 Reviewer", "📦 Aggregator"]
    status_placeholders = []

    for col, name in zip(status_cols, agent_names):
        with col:
            ph = st.empty()
            ph.markdown(f"""
            <div class="agent-card agent-waiting">
                <strong>{name}</strong><br>
                <small>⏳ Waiting</small>
            </div>
            """, unsafe_allow_html=True)
            status_placeholders.append(ph)

    progress_bar = st.progress(0, text="Starting pipeline...")
    output_placeholder = st.empty()

    # ── Run the pipeline ────────────────────────────────────────────
    start_time = time.time()

    try:
        app = get_app(use_memory=True)
        thread_config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        initial_state = {
            "task": task_input.strip(),
            "messages": [],
            "plan": "",
            "research": "",
            "code": "",
            "review": "",
            "final_output": "",
            "next_agent": "",
            "revision_count": 0,
        }

        # ── Stream execution for real-time updates ──────────────────
        result = None
        step_count = 0

        for event in app.stream(initial_state, config=thread_config):
            step_count += 1

            for node_name, node_output in event.items():
                # Update agent status cards
                agent_idx_map = {
                    "planner": 0, "researcher": 1, "coder": 2,
                    "reviewer": 3, "aggregator": 4,
                }

                if node_name in agent_idx_map:
                    idx = agent_idx_map[node_name]

                    # Mark current as done
                    status_placeholders[idx].markdown(f"""
                    <div class="agent-card agent-done">
                        <strong>{agent_names[idx]}</strong><br>
                        <small>✅ Complete</small>
                    </div>
                    """, unsafe_allow_html=True)

                    # Mark next as active (if there is one)
                    next_idx = idx + 1
                    if next_idx < len(status_placeholders):
                        status_placeholders[next_idx].markdown(f"""
                        <div class="agent-card agent-active">
                            <strong>{agent_names[next_idx]}</strong><br>
                            <small>⚡ Running...</small>
                        </div>
                        """, unsafe_allow_html=True)

                # Update progress
                progress = min(step_count / 5.0, 1.0)
                progress_bar.progress(progress, text=f"Running: {node_name}...")

                result = node_output

        elapsed = time.time() - start_time
        progress_bar.progress(1.0, text=f"✅ Complete in {elapsed:.1f}s")

        # ── Get the final state ─────────────────────────────────────
        final_state = app.get_state(thread_config)
        state_values = final_state.values if final_state else {}

        final_output = state_values.get("final_output", "")
        revision_count = state_values.get("revision_count", 0)

        # ── Build agent path ────────────────────────────────────────
        agent_path = []
        if state_values.get("plan"):
            agent_path.append("Planner")
        if state_values.get("research"):
            agent_path.append("Researcher")
        if state_values.get("code"):
            agent_path.append("Coder")
        if state_values.get("review"):
            agent_path.append("Reviewer")
        agent_path.append("Aggregator")

        # ── Display final output ────────────────────────────────────
        st.markdown("### 📋 Final Output")
        st.markdown(final_output if final_output else "⚠️ No output generated.")

        # ── Stats row ───────────────────────────────────────────────
        st.divider()
        stat_cols = st.columns(4)

        with stat_cols[0]:
            st.markdown(f"""
            <div class="stat-card">
                <h3>{elapsed:.1f}s</h3>
                <p>Execution Time</p>
            </div>
            """, unsafe_allow_html=True)

        with stat_cols[1]:
            st.markdown(f"""
            <div class="stat-card">
                <h3>{len(agent_path)}</h3>
                <p>Agents Used</p>
            </div>
            """, unsafe_allow_html=True)

        with stat_cols[2]:
            st.markdown(f"""
            <div class="stat-card">
                <h3>{revision_count}</h3>
                <p>Revisions</p>
            </div>
            """, unsafe_allow_html=True)

        with stat_cols[3]:
            st.markdown(f"""
            <div class="stat-card">
                <h3>{step_count}</h3>
                <p>Graph Steps</p>
            </div>
            """, unsafe_allow_html=True)

        # ── Expandable agent details ────────────────────────────────
        st.divider()
        st.markdown("### 🔍 Agent Details")

        detail_sections = [
            ("🧠 Planner Output", state_values.get("plan", "")),
            ("🔍 Research Findings", state_values.get("research", "")),
            ("💻 Coder Output", state_values.get("code", "")),
            ("🔎 Review Feedback", state_values.get("review", "")),
        ]

        for title, content in detail_sections:
            if content:
                with st.expander(title, expanded=False):
                    st.markdown(content)

        # ── Save to history ─────────────────────────────────────────
        st.session_state.task_history.append({
            "task": task_input.strip(),
            "elapsed": elapsed,
            "revisions": revision_count,
            "path": " → ".join(agent_path),
            "output": final_output,
        })

    except Exception as e:
        st.error(f"❌ Pipeline Error: {e}")
        st.info("💡 Check your `.env` file and API key configuration.")

    finally:
        st.session_state.is_running = False

elif run_button and not task_input.strip():
    st.warning("⚠️ Please enter a task before clicking Run.")
