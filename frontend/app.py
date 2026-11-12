"""
╔══════════════════════════════════════════════════════════════════════╗
║  NEXUS — Multi-Agent Research Platform                              ║
║  Main Streamlit Application                                         ║
║  Premium dark-theme UI with glassmorphism, gradient accents,        ║
║  real-time agent tracking, and a polished portfolio-grade finish.    ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import time
import streamlit as st

# Components build HTML in indented, multi-line strings. Markdown treats indented lines
# after a blank line as a code block, so fragments like "</div>" showed up as text.
# Flatten raw-HTML blocks before rendering; ordinary Markdown is left untouched.
# Streamlit re-runs this script on every interaction, so patch only once.
if not getattr(st.markdown, "_nexus_html_safe", False):
    _st_markdown = st.markdown

    def _markdown_html_safe(body, *args, **kwargs):
        if kwargs.get("unsafe_allow_html") and isinstance(body, str) and body.lstrip().startswith("<"):
            body = "\n".join(line.strip() for line in body.splitlines() if line.strip())
        return _st_markdown(body, *args, **kwargs)

    _markdown_html_safe._nexus_html_safe = True
    st.markdown = _markdown_html_safe

# ── local imports ────────────────────────────────────────────────────
from utils.api_client import NexusAPIClient
from retro_ui import inject_theme, energy_can_egg
from components.header import render_header
from components.research_input import render_research_input
from components.agent_tracker import render_agent_tracker
from components.workflow_graph import render_workflow_graph
from components.report_viewer import render_report
from components.citation_panel import render_citations
from components.analytics import render_analytics
from components.approval_panel import render_approval_panel

# ── page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Research Platform",
    page_icon="🕹️",
    layout="wide",
    initial_sidebar_state="auto",
)

# =====================================================================
#  GLOBAL CSS — dark glassmorphism, gradient buttons, premium polish
# =====================================================================
st.markdown(
    """
    <style>
        /* ── Google Font ─────────────────────────────────────────── */
        

        /* ── base overrides ──────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: 'VT323', monospace !important;
        }

        .stApp {
            background: #0B0420;
        }

        /* ── subtle animated background mesh ─────────────────────── */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background:
                radial-gradient(ellipse at 15% 20%, rgba(0,240,255,0.04) 0%, transparent 50%),
                radial-gradient(ellipse at 85% 80%, rgba(99,179,255,0.03) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(167,139,250,0.02) 0%, transparent 60%);
            animation: bg-drift 30s ease-in-out infinite alternate;
            pointer-events: none;
            z-index: 0;
        }

        @keyframes bg-drift {
            0%   { opacity: 1; }
            50%  { opacity: 0.7; }
            100% { opacity: 1; }
        }

        /* ── scrollbar ───────────────────────────────────────────── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: rgba(0,240,255,0.25);
            border-radius:0;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(0,240,255,0.45);
        }

        /* ── glassmorphism cards ──────────────────────────────────── */
        .glass-card {
            background: linear-gradient(
                145deg,
                rgba(26, 31, 46, 0.75) 0%,
                rgba(11,4,32, 0.88) 100%
            );
            border: 1px solid rgba(0,240,255, 0.12);
            border-radius:0;
            padding: 1.5rem;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow:
                0 8px 32px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.04);
            margin-bottom: 1rem;
        }

        /* ── gradient primary button ─────────────────────────────── */
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #00F0FF 0%, #B26BFF 100%) !important;
            color: #fff !important;
            border: none !important;
            border-radius:0 !important;
            font-family: 'VT323', monospace !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            box-shadow: 0 4px 20px rgba(0,240,255, 0.3) !important;
            transition: all 0.3s ease !important;
        }

        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="baseButton-primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(0,240,255, 0.5) !important;
        }

        /* ── secondary buttons ───────────────────────────────────── */
        .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius:0 !important;
            color: #F2E9FF !important;
            font-family: 'VT323', monospace !important;
            transition: all 0.25s ease !important;
        }

        .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):hover {
            border-color: rgba(0,240,255,0.4) !important;
            background: rgba(0,240,255,0.08) !important;
        }

        /* ── download buttons ────────────────────────────────────── */
        .stDownloadButton > button {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(0,240,255,0.2) !important;
            border-radius:0 !important;
            color: #F2E9FF !important;
            font-family: 'VT323', monospace !important;
            font-weight: 600 !important;
            transition: all 0.25s ease !important;
        }

        .stDownloadButton > button:hover {
            background: rgba(0,240,255,0.1) !important;
            border-color: #00F0FF !important;
        }

        /* ── text inputs / text areas ────────────────────────────── */
        .stTextArea textarea, .stTextInput input {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius:0 !important;
            color: #F2E9FF !important;
            font-family: 'VT323', monospace !important;
            font-size: 0.9rem !important;
        }

        .stTextArea textarea:focus, .stTextInput input:focus {
            border-color: #00F0FF !important;
            box-shadow: 0 0 0 2px rgba(0,240,255,0.15) !important;
        }

        /* ── sliders ─────────────────────────────────────────────── */
        .stSlider [data-testid="stThumbValue"] {
            color: #00F0FF !important;
            font-weight: 700 !important;
        }

        /* ── toggle ──────────────────────────────────────────────── */
        .stToggle label { font-family: 'VT323', monospace !important; }

        /* ── expanders ───────────────────────────────────────────── */
        .streamlit-expanderHeader {
            font-family: 'VT323', monospace !important;
            font-weight: 600 !important;
            background: rgba(255,255,255,0.02) !important;
            border-radius:0 !important;
        }

        /* ── sidebar ─────────────────────────────────────────────── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(
                180deg,
                rgba(11,4,32, 0.98) 0%,
                rgba(26, 31, 46, 0.95) 100%
            ) !important;
            border-right: 1px solid rgba(0,240,255,0.08) !important;
        }

        section[data-testid="stSidebar"] .stMarkdown {
            font-family: 'VT323', monospace !important;
        }

        /* ── metrics ─────────────────────────────────────────────── */
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius:0;
            padding: 0.8rem !important;
        }

        [data-testid="stMetricValue"] {
            font-family: 'VT323', monospace !important;
            font-weight: 800 !important;
            color: #00F0FF !important;
        }

        /* ── radio pills ─────────────────────────────────────────── */
        .stRadio > div { gap: 0.5rem !important; }
        .stRadio > div > label {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius:0 !important;
            padding: 0.5rem 1rem !important;
            font-family: 'VT323', monospace !important;
            transition: all 0.2s ease !important;
        }
        .stRadio > div > label[data-checked="true"],
        .stRadio > div > label:has(input:checked) {
            border-color: #00F0FF !important;
            background: rgba(0,240,255,0.1) !important;
        }

        /* ── pulse keyframe (reusable) ───────────────────────────── */
        @keyframes soft-pulse {
            0%, 100% { opacity: 1; }
            50%      { opacity: 0.5; }
        }

        /* ── hide Streamlit branding ─────────────────────────────── */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background: transparent; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Retro arcade theme: loads after the base CSS so it wins.
inject_theme()
with st.sidebar:
    st.markdown(
        """
        <div class="px-title neon-m" style="font-size:0.8rem;margin:0.4rem 0 0.8rem">HOW TO PLAY</div>
        <div style="font-size:1.25rem;line-height:1.5">
        <span class="neon-y">1.</span> Type your research quest<br/>
        <span class="neon-y">2.</span> Pick a difficulty<br/>
        <span class="neon-y">3.</span> Press START and watch your party<br/>
        <span class="neon-y">4.</span> Beat the Critic, claim your report
        </div>
        """,
        unsafe_allow_html=True,
    )
    energy_can_egg(st)


# =====================================================================
#  SESSION STATE INITIALISATION
# =====================================================================
_DEFAULTS = {
    "task_id": None,
    "task_status": None,       # raw status dict from backend
    "phase": "idle",           # idle | running | needs_approval | completed | failed
    "report_data": None,
    "metrics_data": {},
    "recent_tasks": [],
    "polling": False,
    "backend_url": os.getenv("NEXUS_BACKEND_URL", "http://localhost:8000"),
}

for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── API client (cached on base URL) ─────────────────────────────────
@st.cache_resource
def _get_client(base_url: str) -> NexusAPIClient:
    return NexusAPIClient(base_url=base_url)


api = _get_client(st.session_state.backend_url)


# =====================================================================
#  HELPERS
# =====================================================================
def _poll_status() -> None:
    """Fetch latest task status from backend and update session state."""
    tid = st.session_state.task_id
    if not tid:
        return

    try:
        data = api.get_task_status(tid)
        st.session_state.task_status = data
        status_str = data.get("status", "unknown").lower()

        if status_str == "completed":
            st.session_state.phase = "completed"
            st.session_state.polling = False
            try:
                st.session_state.report_data = api.get_report(tid)
            except RuntimeError:
                st.session_state.report_data = None
        elif status_str == "needs_approval":
            st.session_state.phase = "needs_approval"
            st.session_state.polling = False
        elif status_str == "failed":
            st.session_state.phase = "failed"
            st.session_state.polling = False
        else:
            st.session_state.phase = "running"
            st.session_state.polling = True

        # update metrics
        try:
            st.session_state.metrics_data = api.get_metrics()
        except RuntimeError:
            pass

    except RuntimeError as exc:
        st.error(str(exc))
        st.session_state.polling = False


def _add_recent_task(task_id: str, query: str) -> None:
    entry = {"id": task_id, "query": query[:80], "ts": time.strftime("%H:%M:%S")}
    tasks = st.session_state.recent_tasks
    tasks.insert(0, entry)
    st.session_state.recent_tasks = tasks[:10]


def _reset_session() -> None:
    st.session_state.task_id = None
    st.session_state.task_status = None
    st.session_state.phase = "idle"
    st.session_state.report_data = None
    st.session_state.polling = False


# =====================================================================
#  HEADER
# =====================================================================
health = api.get_health()
is_connected = health.get("status", "unreachable") != "unreachable"
render_header(connected=is_connected)


# =====================================================================
#  MAIN LAYOUT
# =====================================================================
main_col, sidebar_col = st.columns([7, 3], gap="large")


# ─────────────────────────────────────────────────────────────────────
#  LEFT COLUMN — primary content area
# ─────────────────────────────────────────────────────────────────────
with main_col:

    # ── IDLE: show research input ────────────────────────────────────
    if st.session_state.phase == "idle":
        config = render_research_input()

        if config is not None:
            try:
                result = api.start_research(
                    query=config.query,
                    depth=config.depth,
                    max_sources=config.max_sources,
                    require_approval=config.require_approval,
                    include_code_analysis=config.include_code_analysis,
                )
                st.session_state.task_id = result.get("task_id", result.get("id"))
                st.session_state.phase = "running"
                st.session_state.polling = True
                _add_recent_task(st.session_state.task_id, config.query)
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))

    # ── RUNNING: show agent tracker + workflow graph ──────────────────
    elif st.session_state.phase == "running":
        status_data = st.session_state.task_status or {}

        st.markdown(
            """
            <div style="
                display:flex; align-items:center; gap:0.6rem;
                margin-bottom:1rem;
            ">
                <div style="
                    width:10px; height:10px; border-radius:0;
                    background:#00F0FF;
                    animation: soft-pulse 1.5s ease-in-out infinite;
                "></div>
                <span style="
                    font-family:'VT323', monospace; font-size:0.85rem;
                    font-weight:600; color:#00F0FF;
                ">Research in progress…</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_agent_tracker(status_data)
        render_workflow_graph(status_data)

        # new-task button during run
        if st.button("✖  Abort Quest", key="cancel_btn"):
            _reset_session()
            st.rerun()

    # ── NEEDS APPROVAL: show report preview + approval panel ─────────
    elif st.session_state.phase == "needs_approval":
        status_data = st.session_state.task_status or {}
        review_data = status_data.get("review", {})

        st.markdown(
            """
            <div style="
                display:flex; align-items:center; gap:0.6rem;
                padding:0.7rem 1rem; margin-bottom:1rem;
                background:rgba(255,230,0,0.08);
                border:1px solid rgba(255,230,0,0.25);
                border-radius:0;
            ">
                <span style="font-size:1.2rem;">⏸️</span>
                <span style="
                    font-family:'VT323', monospace; font-size:0.85rem;
                    font-weight:600; color:#FFE600;
                ">Awaiting your approval before finalising the report</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        action = render_approval_panel(
            task_id=st.session_state.task_id,
            review_data=review_data,
            api_client=api,
        )

        if action == "approved":
            st.session_state.phase = "completed"
            try:
                st.session_state.report_data = api.get_report(st.session_state.task_id)
            except RuntimeError:
                pass
            st.rerun()
        elif action == "revised":
            st.session_state.phase = "running"
            st.session_state.polling = True
            st.rerun()
        elif action == "rejected":
            _reset_session()
            st.rerun()

    # ── COMPLETED: show full report + citations ──────────────────────
    elif st.session_state.phase == "completed":
        report = st.session_state.report_data or {}

        st.markdown(
            """
            <div style="
                display:flex; align-items:center; gap:0.6rem;
                padding:0.7rem 1rem; margin-bottom:1rem;
                background:rgba(57,255,20,0.06);
                border:1px solid rgba(57,255,20,0.2);
                border-radius:0;
            ">
                <span style="font-size:1.2rem;">✅</span>
                <span style="
                    font-family:'VT323', monospace; font-size:0.85rem;
                    font-weight:600; color:#39FF14;
                ">Research complete — report ready</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if report:
            render_report(report)
            citations = report.get("citations", [])
            sources = report.get("sources", [])
            if citations:
                render_citations(citations, sources)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        if st.button("▶  New Quest", type="primary", key="new_research_btn"):
            _reset_session()
            st.rerun()

    # ── FAILED ───────────────────────────────────────────────────────
    elif st.session_state.phase == "failed":
        status_data = st.session_state.task_status or {}
        error_msg = status_data.get("error", "An unknown error occurred during research.")

        st.markdown(
            f"""
            <div style="
                padding:1.5rem; margin-bottom:1rem;
                background:rgba(255,51,85,0.06);
                border:1px solid rgba(255,51,85,0.2);
                border-radius:0;
            ">
                <div style="
                    font-family:'VT323', monospace; font-size:1.1rem;
                    font-weight:700; color:#FF3355; margin-bottom:0.4rem;
                ">💥 Research Failed</div>
                <div style="
                    font-family:'VT323', monospace; font-size:0.85rem;
                    color:rgba(242,233,255,0.6); line-height:1.6;
                ">{error_msg}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # show partial tracker if we have agent data
        if status_data.get("agents"):
            render_agent_tracker(status_data)

        if st.button("🔄  Try Again", type="primary", key="retry_btn"):
            _reset_session()
            st.rerun()


# ─────────────────────────────────────────────────────────────────────
#  RIGHT COLUMN — sidebar analytics & meta
# ─────────────────────────────────────────────────────────────────────
with sidebar_col:

    # ── analytics ────────────────────────────────────────────────────
    metrics = st.session_state.metrics_data or {}
    if st.session_state.phase != "idle":
        # pull agent-level metrics from task_status if global metrics are empty
        if not metrics.get("agents") and st.session_state.task_status:
            metrics = {
                "agents": st.session_state.task_status.get("agents", {}),
                "total_tokens": sum(
                    a.get("tokens", 0)
                    for a in st.session_state.task_status.get("agents", {}).values()
                ),
                "total_cost_usd": sum(
                    a.get("cost_usd", 0)
                    for a in st.session_state.task_status.get("agents", {}).values()
                ),
                "total_latency_ms": sum(
                    a.get("latency_ms", 0)
                    for a in st.session_state.task_status.get("agents", {}).values()
                ),
                "revision_count": st.session_state.task_status.get("revision_count", 0),
                "quality_scores": st.session_state.task_status.get("quality_scores", []),
            }
        render_analytics(metrics)

    # ── health status ────────────────────────────────────────────────
    st.markdown(
        """
        <p style="
            font-family:'VT323', monospace; font-weight:700; font-size:1rem;
            color:#F2E9FF; margin-top:1rem; margin-bottom:0.6rem;
        ">🏥 System Health</p>
        """,
        unsafe_allow_html=True,
    )

    health_color = "#39FF14" if is_connected else "#FF3355"
    health_status = health.get("status", "unreachable")
    health_latency = health.get("latency_ms")

    st.markdown(
        f"""
        <div style="
            display:flex; align-items:center; gap:0.5rem;
            padding:0.6rem 0.9rem;
            background:rgba(255,255,255,0.02);
            border:1px solid rgba(255,255,255,0.06);
            border-radius:0;
            margin-bottom:0.5rem;
        ">
            <div style="
                width:8px; height:8px; border-radius:0;
                background:{health_color};
                box-shadow:0 0 8px {health_color}80;
            "></div>
            <span style="
                font-family:'VT323', monospace; font-size:0.8rem;
                font-weight:600; color:{health_color};
                text-transform:uppercase; letter-spacing:1px;
            ">{health_status}</span>
            {'<span style="font-family:VT323,monospace;font-size:0.7rem;color:rgba(242,233,255,0.35);margin-left:auto;">' + str(health_latency) + 'ms</span>' if health_latency else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── recent tasks ─────────────────────────────────────────────────
    recent = st.session_state.recent_tasks
    if recent:
        st.markdown(
            """
            <p style="
                font-family:'VT323', monospace; font-weight:700; font-size:1rem;
                color:#F2E9FF; margin-top:1.2rem; margin-bottom:0.6rem;
            ">🕘 Recent Tasks</p>
            """,
            unsafe_allow_html=True,
        )

        for task in recent[:5]:
            tid_short = task["id"][:8] if task.get("id") else "—"
            st.markdown(
                f"""
                <div style="
                    padding:0.55rem 0.8rem;
                    background:rgba(255,255,255,0.02);
                    border:1px solid rgba(255,255,255,0.04);
                    border-radius:0;
                    margin-bottom:0.4rem;
                    cursor:pointer;
                    transition:border-color 0.2s;
                " onmouseover="this.style.borderColor='rgba(0,240,255,0.3)'"
                   onmouseout="this.style.borderColor='rgba(255,255,255,0.04)'">
                    <div style="
                        font-family:'VT323', monospace; font-size:0.78rem;
                        color:rgba(242,233,255,0.65); white-space:nowrap;
                        overflow:hidden; text-overflow:ellipsis;
                    ">{task.get('query', '')}</div>
                    <div style="
                        display:flex; justify-content:space-between;
                        margin-top:0.2rem;
                    ">
                        <span style="
                            font-family:'VT323', monospace; font-size:0.62rem;
                            color:rgba(0,240,255,0.5);
                        ">{tid_short}</span>
                        <span style="
                            font-family:'VT323', monospace; font-size:0.62rem;
                            color:rgba(242,233,255,0.25);
                        ">{task.get('ts', '')}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── backend URL config (collapsed) ──────────────────────────────
    with st.expander("⚙️ Settings", expanded=False):
        new_url = st.text_input(
            "Backend URL",
            value=st.session_state.backend_url,
            key="settings_url",
        )
        if new_url != st.session_state.backend_url:
            st.session_state.backend_url = new_url
            st.cache_resource.clear()
            st.rerun()

    # ── footer branding ──────────────────────────────────────────────
    st.markdown(
        """
        <div style="
            text-align:center; padding:2rem 0 1rem 0;
            font-family:'VT323', monospace; font-size:0.65rem;
            color:rgba(242,233,255,0.15); letter-spacing:1px;
        ">
            NEXUS RESEARCH PLATFORM · v1.0
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
#  AUTO-POLLING (runs at end of script to trigger rerun when active)
# =====================================================================
if st.session_state.polling and st.session_state.task_id:
    _poll_status()
    time.sleep(2)
    st.rerun()
