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

# ── local imports ────────────────────────────────────────────────────
from utils.api_client import NexusAPIClient
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
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
#  GLOBAL CSS — dark glassmorphism, gradient buttons, premium polish
# =====================================================================
st.markdown(
    """
    <style>
        /* ── Google Font ─────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* ── base overrides ──────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }

        .stApp {
            background: #0E1117;
        }

        /* ── subtle animated background mesh ─────────────────────── */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background:
                radial-gradient(ellipse at 15% 20%, rgba(108,99,255,0.04) 0%, transparent 50%),
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
            background: rgba(108,99,255,0.25);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(108,99,255,0.45);
        }

        /* ── glassmorphism cards ──────────────────────────────────── */
        .glass-card {
            background: linear-gradient(
                145deg,
                rgba(26, 31, 46, 0.75) 0%,
                rgba(14, 17, 23, 0.88) 100%
            );
            border: 1px solid rgba(108, 99, 255, 0.12);
            border-radius: 16px;
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
            background: linear-gradient(135deg, #6C63FF 0%, #5A4FCF 100%) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 12px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            box-shadow: 0 4px 20px rgba(108, 99, 255, 0.3) !important;
            transition: all 0.3s ease !important;
        }

        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="baseButton-primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(108, 99, 255, 0.5) !important;
        }

        /* ── secondary buttons ───────────────────────────────────── */
        .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 10px !important;
            color: #E0E0E0 !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.25s ease !important;
        }

        .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):hover {
            border-color: rgba(108,99,255,0.4) !important;
            background: rgba(108,99,255,0.08) !important;
        }

        /* ── download buttons ────────────────────────────────────── */
        .stDownloadButton > button {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(108,99,255,0.2) !important;
            border-radius: 10px !important;
            color: #E0E0E0 !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            transition: all 0.25s ease !important;
        }

        .stDownloadButton > button:hover {
            background: rgba(108,99,255,0.1) !important;
            border-color: #6C63FF !important;
        }

        /* ── text inputs / text areas ────────────────────────────── */
        .stTextArea textarea, .stTextInput input {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 12px !important;
            color: #E0E0E0 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.9rem !important;
        }

        .stTextArea textarea:focus, .stTextInput input:focus {
            border-color: #6C63FF !important;
            box-shadow: 0 0 0 2px rgba(108,99,255,0.15) !important;
        }

        /* ── sliders ─────────────────────────────────────────────── */
        .stSlider [data-testid="stThumbValue"] {
            color: #6C63FF !important;
            font-weight: 700 !important;
        }

        /* ── toggle ──────────────────────────────────────────────── */
        .stToggle label { font-family: 'Inter', sans-serif !important; }

        /* ── expanders ───────────────────────────────────────────── */
        .streamlit-expanderHeader {
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            background: rgba(255,255,255,0.02) !important;
            border-radius: 10px !important;
        }

        /* ── sidebar ─────────────────────────────────────────────── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(
                180deg,
                rgba(14, 17, 23, 0.98) 0%,
                rgba(26, 31, 46, 0.95) 100%
            ) !important;
            border-right: 1px solid rgba(108,99,255,0.08) !important;
        }

        section[data-testid="stSidebar"] .stMarkdown {
            font-family: 'Inter', sans-serif !important;
        }

        /* ── metrics ─────────────────────────────────────────────── */
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 0.8rem !important;
        }

        [data-testid="stMetricValue"] {
            font-family: 'Inter', sans-serif !important;
            font-weight: 800 !important;
            color: #6C63FF !important;
        }

        /* ── radio pills ─────────────────────────────────────────── */
        .stRadio > div { gap: 0.5rem !important; }
        .stRadio > div > label {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 10px !important;
            padding: 0.5rem 1rem !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.2s ease !important;
        }
        .stRadio > div > label[data-checked="true"],
        .stRadio > div > label:has(input:checked) {
            border-color: #6C63FF !important;
            background: rgba(108,99,255,0.1) !important;
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
                    width:10px; height:10px; border-radius:50%;
                    background:#6C63FF;
                    animation: soft-pulse 1.5s ease-in-out infinite;
                "></div>
                <span style="
                    font-family:'Inter',sans-serif; font-size:0.85rem;
                    font-weight:600; color:#6C63FF;
                ">Research in progress…</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_agent_tracker(status_data)
        render_workflow_graph(status_data)

        # new-task button during run
        if st.button("🛑  Cancel & Start New Research", key="cancel_btn"):
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
                background:rgba(255,152,0,0.08);
                border:1px solid rgba(255,152,0,0.25);
                border-radius:12px;
            ">
                <span style="font-size:1.2rem;">⏸️</span>
                <span style="
                    font-family:'Inter',sans-serif; font-size:0.85rem;
                    font-weight:600; color:#FF9800;
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
                background:rgba(0,230,118,0.06);
                border:1px solid rgba(0,230,118,0.2);
                border-radius:12px;
            ">
                <span style="font-size:1.2rem;">✅</span>
                <span style="
                    font-family:'Inter',sans-serif; font-size:0.85rem;
                    font-weight:600; color:#00E676;
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
        if st.button("🔬  Start New Research", type="primary", key="new_research_btn"):
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
                background:rgba(255,82,82,0.06);
                border:1px solid rgba(255,82,82,0.2);
                border-radius:14px;
            ">
                <div style="
                    font-family:'Inter',sans-serif; font-size:1.1rem;
                    font-weight:700; color:#FF5252; margin-bottom:0.4rem;
                ">💥 Research Failed</div>
                <div style="
                    font-family:'Inter',sans-serif; font-size:0.85rem;
                    color:rgba(224,224,224,0.6); line-height:1.6;
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
            font-family:'Inter',sans-serif; font-weight:700; font-size:1rem;
            color:#E0E0E0; margin-top:1rem; margin-bottom:0.6rem;
        ">🏥 System Health</p>
        """,
        unsafe_allow_html=True,
    )

    health_color = "#00E676" if is_connected else "#FF5252"
    health_status = health.get("status", "unreachable")
    health_latency = health.get("latency_ms")

    st.markdown(
        f"""
        <div style="
            display:flex; align-items:center; gap:0.5rem;
            padding:0.6rem 0.9rem;
            background:rgba(255,255,255,0.02);
            border:1px solid rgba(255,255,255,0.06);
            border-radius:10px;
            margin-bottom:0.5rem;
        ">
            <div style="
                width:8px; height:8px; border-radius:50%;
                background:{health_color};
                box-shadow:0 0 8px {health_color}80;
            "></div>
            <span style="
                font-family:'Inter',sans-serif; font-size:0.8rem;
                font-weight:600; color:{health_color};
                text-transform:uppercase; letter-spacing:1px;
            ">{health_status}</span>
            {'<span style="font-family:Inter,sans-serif;font-size:0.7rem;color:rgba(224,224,224,0.35);margin-left:auto;">' + str(health_latency) + 'ms</span>' if health_latency else ''}
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
                font-family:'Inter',sans-serif; font-weight:700; font-size:1rem;
                color:#E0E0E0; margin-top:1.2rem; margin-bottom:0.6rem;
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
                    border-radius:8px;
                    margin-bottom:0.4rem;
                    cursor:pointer;
                    transition:border-color 0.2s;
                " onmouseover="this.style.borderColor='rgba(108,99,255,0.3)'"
                   onmouseout="this.style.borderColor='rgba(255,255,255,0.04)'">
                    <div style="
                        font-family:'Inter',sans-serif; font-size:0.78rem;
                        color:rgba(224,224,224,0.65); white-space:nowrap;
                        overflow:hidden; text-overflow:ellipsis;
                    ">{task.get('query', '')}</div>
                    <div style="
                        display:flex; justify-content:space-between;
                        margin-top:0.2rem;
                    ">
                        <span style="
                            font-family:'Inter',monospace; font-size:0.62rem;
                            color:rgba(108,99,255,0.5);
                        ">{tid_short}</span>
                        <span style="
                            font-family:'Inter',sans-serif; font-size:0.62rem;
                            color:rgba(224,224,224,0.25);
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
            font-family:'Inter',sans-serif; font-size:0.65rem;
            color:rgba(224,224,224,0.15); letter-spacing:1px;
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
