"""
Nexus Research Platform — Agent Tracker Component
Renders the agent pipeline with live status, reasoning traces, and metrics.
"""

import streamlit as st

from retro_ui import pixel_svg, xp_bar

_XP = {"pending": 0.0, "active": 0.6, "completed": 1.0, "failed": 1.0}
from typing import Any


# ── Agent pipeline definition ────────────────────────────────────────
PIPELINE_AGENTS = [
    {"key": "planner", "label": "Planner", "icon": "📋", "sprite": "star", "cls": "STRATEGIST", "desc": "Decompose query into sub-tasks"},
    {"key": "researcher", "label": "Researcher", "icon": "🔎", "sprite": "rocket", "cls": "SCOUT", "desc": "Gather sources & evidence"},
    {"key": "analyst", "label": "Analyst", "icon": "📊", "sprite": "cat", "cls": "SAGE", "desc": "Synthesise & cross-reference"},
    {"key": "writer", "label": "Writer", "icon": "✍️", "sprite": "heart", "cls": "BARD", "desc": "Draft the research report"},
    {"key": "critic", "label": "Critic", "icon": "🧪", "sprite": "joystick", "cls": "BOSS", "desc": "Review, score & iterate"},
]


def _status_style(status: str) -> dict:
    """Return colour & animation metadata for a given status."""
    styles = {
        "pending":   {"bg": "rgba(255,255,255,0.03)", "border": "rgba(255,255,255,0.08)", "text": "#B8ADD6", "glow": "none", "anim": ""},
        "active":    {"bg": "rgba(0,240,255,0.10)", "border": "#00F0FF", "text": "#00F0FF", "glow": "0 0 24px rgba(0,240,255,0.35)", "anim": "agent-pulse 2s ease-in-out infinite"},
        "completed": {"bg": "rgba(57,255,20,0.08)", "border": "rgba(57,255,20,0.5)", "text": "#39FF14", "glow": "0 0 12px rgba(57,255,20,0.2)", "anim": ""},
        "failed":    {"bg": "rgba(255,51,85,0.08)", "border": "rgba(255,51,85,0.5)", "text": "#FF3355", "glow": "0 0 12px rgba(255,51,85,0.2)", "anim": ""},
    }
    return styles.get(status, styles["pending"])


def _status_badge(status: str) -> str:
    labels = {
        "pending": "WAITING",
        "active": "IN BATTLE",
        "completed": "LEVEL UP",
        "failed": "K.O.",
    }
    return labels.get(status, status.upper())


def render_agent_tracker(status_data: dict) -> None:
    """
    Render the five-stage agent pipeline with live status indicators.

    Expected *status_data* shape::

        {
            "agents": {
                "planner":    {"status": "completed", "tokens": 1240, "latency_ms": 3200, "reasoning": "..."},
                "researcher": {"status": "active",    "tokens": 870,  "latency_ms": 0,    "reasoning": "..."},
                ...
            }
        }
    """

    agents_info: dict = status_data.get("agents", {})

    # ── inject keyframe once ────────────────────────────────────────
    st.markdown(
        """
        <style>
            @keyframes agent-pulse {
                0%, 100% { box-shadow: 0 0 8px rgba(0,240,255,0.2); }
                50%      { box-shadow: 0 0 28px rgba(0,240,255,0.55); }
            }
            @keyframes spin-icon {
                0%   { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .tracker-title {
                font-family: 'VT323', monospace;
                font-weight: 700;
                font-size: 1.1rem;
                color: #F2E9FF;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .pipeline-wrap {
                display: flex;
                align-items: stretch;
                gap: 0;
                margin-bottom: 1.5rem;
                overflow-x: auto;
                padding-bottom: 0.5rem;
            }

            .agent-node {
                flex: 1;
                min-width: 140px;
                padding: 1.1rem 0.9rem;
                border-radius:0;
                text-align: center;
                position: relative;
                transition: all 0.35s ease;
            }

            .agent-connector {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 36px;
                min-width: 36px;
                color: rgba(255,255,255,0.12);
                font-size: 1.2rem;
            }

            .agent-connector.done { color: #39FF14; }
            .agent-connector.active-conn { color: #00F0FF; }

            .agent-icon { height: 48px; display:flex; align-items:flex-end; justify-content:center; margin-bottom: 0.35rem; }
            .agent-class { font-family:'Press Start 2P',monospace; font-size:0.55rem; color:#FFE600; margin:4px 0 6px; letter-spacing:1px; }

            .agent-label {
                font-family: 'VT323', monospace;
                font-weight: 600;
                font-size: 0.82rem;
                margin-bottom: 0.15rem;
            }

            .agent-desc {
                font-family: 'VT323', monospace;
                font-size: 0.65rem;
                color: rgba(242,233,255,0.35);
                margin-bottom: 0.5rem;
            }

            .agent-badge {
                display: inline-block;
                font-family: 'VT323', monospace;
                font-size: 0.6rem;
                font-weight: 700;
                letter-spacing: 1px;
                padding: 0.2rem 0.55rem;
                border-radius:0;
                text-transform: uppercase;
            }

            .agent-metrics {
                margin-top: 0.5rem;
                display: flex;
                justify-content: center;
                gap: 0.7rem;
            }

            .agent-metric-item {
                font-family: 'VT323', monospace;
                font-size: 0.62rem;
                color: rgba(242,233,255,0.4);
            }

            .agent-metric-val {
                font-weight: 700;
                color: rgba(242,233,255,0.65);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="tracker-title">&#9654; PARTY STATUS</div>',
        unsafe_allow_html=True,
    )

    # ── build pipeline HTML ─────────────────────────────────────────
    html_parts: list[str] = ['<div class="pipeline-wrap">']

    for idx, agent_def in enumerate(PIPELINE_AGENTS):
        key = agent_def["key"]
        info = agents_info.get(key, {})
        status = info.get("status", "pending")
        tokens = info.get("tokens", 0)
        latency = info.get("latency_ms", 0)

        s = _status_style(status)

        node_style = (
            f"background:{s['bg']};"
            f"border:1px solid {s['border']};"
            f"box-shadow:{s['glow']};"
        )
        if s["anim"]:
            node_style += f"animation:{s['anim']};"

        badge_style = (
            f"background:{s['bg']};color:{s['text']};"
            f"border:1px solid {s['border']};"
        )

        latency_str = f"{latency / 1000:.1f}s" if latency else "—"
        tokens_str = f"{tokens:,}" if tokens else "—"

        html_parts.append(
            f"""
            <div class="agent-node" style="{node_style}">
                <div class="agent-icon">{pixel_svg(agent_def['sprite'], 4)}</div>
                <div class="agent-label" style="color:{s['text']}">{agent_def['label']}</div>
                <div class="agent-class">LV.{idx + 1} {agent_def['cls']}</div>
                {xp_bar(_XP.get(status, 0.0), s['text'] if status != 'pending' else '#5B3FB5')}
                <div class="agent-desc">{agent_def['desc']}</div>
                <span class="agent-badge" style="{badge_style}">{_status_badge(status)}</span>
                <div class="agent-metrics">
                    <span class="agent-metric-item">
                        <span class="agent-metric-val">{tokens_str}</span> tok
                    </span>
                    <span class="agent-metric-item">
                        <span class="agent-metric-val">{latency_str}</span>
                    </span>
                </div>
            </div>
            """
        )

        # connector arrow between nodes
        if idx < len(PIPELINE_AGENTS) - 1:
            next_key = PIPELINE_AGENTS[idx + 1]["key"]
            next_status = agents_info.get(next_key, {}).get("status", "pending")
            conn_class = "agent-connector"
            if status == "completed":
                conn_class += " done"
            elif status == "active" or next_status == "active":
                conn_class += " active-conn"
            html_parts.append(
                f'<div class="{conn_class}">→</div>'
            )

    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)

    # ── reasoning traces ────────────────────────────────────────────
    has_any_reasoning = any(
        agents_info.get(a["key"], {}).get("reasoning") for a in PIPELINE_AGENTS
    )

    if has_any_reasoning:
        st.markdown(
            "<p style='font-family:VT323,monospace;font-size:0.85rem;"
            "font-weight:600;color:#F2E9FF;margin-bottom:0.4rem;'>"
            "💭 Agent Reasoning Traces</p>",
            unsafe_allow_html=True,
        )

        for agent_def in PIPELINE_AGENTS:
            info = agents_info.get(agent_def["key"], {})
            reasoning = info.get("reasoning", "")
            status = info.get("status", "pending")
            if not reasoning:
                continue

            s = _status_style(status)
            with st.expander(
                f"{agent_def['icon']} {agent_def['label']} — {_status_badge(status)}",
                expanded=(status == "active"),
            ):
                st.markdown(
                    f"""
                    <div style="
                        font-family: 'VT323', monospace;
                        font-size: 0.78rem;
                        line-height: 1.6;
                        color: rgba(242,233,255,0.7);
                        padding: 0.8rem;
                        background: rgba(0,0,0,0.2);
                        border-radius:0;
                        border-left: 3px solid {s['border']};
                        max-height: 300px;
                        overflow-y: auto;
                    ">{reasoning}</div>
                    """,
                    unsafe_allow_html=True,
                )

                metrics_cols = st.columns(3)
                with metrics_cols[0]:
                    st.metric("Tokens", f"{info.get('tokens', 0):,}")
                with metrics_cols[1]:
                    lat = info.get("latency_ms", 0)
                    st.metric("Latency", f"{lat / 1000:.1f}s" if lat else "—")
                with metrics_cols[2]:
                    st.metric("Status", _status_badge(status))
