"""
Nexus Research Platform — Research Input Component
Premium research configuration form with glassmorphism styling.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResearchConfig:
    """Typed container for research parameters."""
    query: str
    depth: str
    max_sources: int
    require_approval: bool
    include_code_analysis: bool


_DEPTH_OPTIONS = {
    "quick": {
        "label": "⚡ Easy",
        "desc": "Fast sweep — 2-3 min, surface-level overview",
        "icon": "⚡",
    },
    "standard": {
        "label": "🔍 Normal",
        "desc": "Balanced depth — 5-8 min, thorough analysis",
        "icon": "🔍",
    },
    "deep": {
        "label": "🧬 Hard",
        "desc": "Exhaustive research — 10-20 min, maximum rigour",
        "icon": "🧬",
    },
}


def render_research_input() -> Optional[ResearchConfig]:
    """
    Render the research configuration card.
    Returns a ResearchConfig when the user clicks Launch, else None.
    """

    # ── inject card CSS ─────────────────────────────────────────────
    st.markdown(
        """
        <style>
            .research-card {
                background: linear-gradient(
                    145deg,
                    rgba(26, 31, 46, 0.85) 0%,
                    rgba(11,4,32, 0.92) 100%
                );
                border: 1px solid rgba(0,240,255, 0.15);
                border-radius:0;
                padding: 2rem 2rem 1.5rem 2rem;
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                box-shadow:
                    0 8px 32px rgba(0, 0, 0, 0.35),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05);
                margin-bottom: 1.5rem;
            }

            .research-card-title {
                font-family: 'VT323', monospace;
                font-weight: 700;
                font-size: 1.25rem;
                color: #F2E9FF;
                margin-bottom: 0.3rem;
            }

            .research-card-sub {
                font-family: 'VT323', monospace;
                font-size: 0.82rem;
                color: rgba(242,233,255, 0.45);
                margin-bottom: 1.2rem;
            }

            .depth-grid {
                display: flex;
                gap: 0.75rem;
                margin-bottom: 0.5rem;
            }

            .depth-opt {
                flex: 1;
                padding: 0.9rem 0.8rem;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius:0;
                text-align: center;
                cursor: pointer;
                transition: all 0.25s ease;
            }

            .depth-opt:hover {
                border-color: rgba(0,240,255, 0.4);
                background: rgba(0,240,255, 0.06);
            }

            .depth-opt.active {
                border-color: #00F0FF;
                background: rgba(0,240,255, 0.12);
                box-shadow: 0 0 20px rgba(0,240,255, 0.15);
            }

            .depth-icon { font-size: 1.4rem; margin-bottom: 0.25rem; }

            .depth-label {
                font-family: 'VT323', monospace;
                font-weight: 600;
                font-size: 0.82rem;
                color: #F2E9FF;
            }

            .depth-desc {
                font-family: 'VT323', monospace;
                font-size: 0.7rem;
                color: rgba(242,233,255, 0.4);
                margin-top: 0.2rem;
            }

            div.stButton > button.launch-btn {
                width: 100%;
                padding: 0.85rem 2rem;
                background: linear-gradient(135deg, #00F0FF 0%, #B26BFF 100%);
                color: #fff;
                font-family: 'VT323', monospace;
                font-weight: 700;
                font-size: 1rem;
                letter-spacing: 1.5px;
                border: none;
                border-radius:0;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 20px rgba(0,240,255, 0.35);
                text-transform: uppercase;
            }

            div.stButton > button.launch-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 30px rgba(0,240,255, 0.5);
            }

            .toggle-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.5rem 0;
            }

            .toggle-label {
                font-family: 'VT323', monospace;
                font-size: 0.85rem;
                color: #F2E9FF;
            }

            .toggle-hint {
                font-family: 'VT323', monospace;
                font-size: 0.7rem;
                color: rgba(242,233,255,0.35);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── card header ─────────────────────────────────────────────────
    st.markdown(
        """
        <div class="research-card">
            <div class="research-card-title">&#9654; NEW QUEST</div>
            <div class="research-card-sub">
                Name your quest. Your five-agent party handles the rest.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── query input ─────────────────────────────────────────────────
    query = st.text_area(
        "Research Query",
        placeholder=(
            "Enter your research question...\n\n"
            "Example: What are the latest advances in quantum error correction, "
            "and how do surface codes compare to color codes for near-term devices?"
        ),
        height=130,
        label_visibility="collapsed",
    )

    # ── depth selector ──────────────────────────────────────────────
    st.markdown(
        "<p style='font-family:VT323,monospace;font-size:0.85rem;"
        "font-weight:600;color:#F2E9FF;margin-bottom:0.3rem;'>"
        "Research Depth</p>",
        unsafe_allow_html=True,
    )

    depth_keys = list(_DEPTH_OPTIONS.keys())
    depth_labels = [v["label"] for v in _DEPTH_OPTIONS.values()]
    selected_depth = st.radio(
        "Research Depth",
        depth_keys,
        format_func=lambda k: _DEPTH_OPTIONS[k]["label"],
        horizontal=True,
        index=1,
        label_visibility="collapsed",
    )

    depth_info = _DEPTH_OPTIONS[selected_depth]
    st.caption(f"{depth_info['desc']}")

    # ── max sources slider ──────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        max_sources = st.slider(
            "Maximum Sources",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="Number of sources the research agents will consult.",
        )

    with col2:
        st.markdown(
            f"""
            <div style="
                margin-top: 1.1rem;
                padding: 0.7rem 1rem;
                background: rgba(0,240,255,0.08);
                border: 1px solid rgba(0,240,255,0.15);
                border-radius:0;
                text-align: center;
            ">
                <span style="
                    font-family: 'VT323', monospace;
                    font-size: 1.5rem;
                    font-weight: 800;
                    color: #00F0FF;
                ">{max_sources}</span>
                <br/>
                <span style="
                    font-family: 'VT323', monospace;
                    font-size: 0.7rem;
                    color: rgba(242,233,255,0.4);
                    text-transform: uppercase;
                    letter-spacing: 1px;
                ">sources</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── toggles ─────────────────────────────────────────────────────
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    toggle_col1, toggle_col2 = st.columns(2)
    with toggle_col1:
        require_approval = st.toggle(
            "🛡️ Human Approval Gate",
            value=False,
            help="Pause before finalising so you can review the draft.",
        )
    with toggle_col2:
        include_code = st.toggle(
            "💻 Include Code Analysis",
            value=False,
            help="Enable the code-analysis agent for technical queries.",
        )

    # ── launch button ───────────────────────────────────────────────
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    launched = st.button(
        "▶  PRESS START",
        use_container_width=True,
        type="primary",
    )

    if launched and query.strip():
        return ResearchConfig(
            query=query.strip(),
            depth=selected_depth,
            max_sources=max_sources,
            require_approval=require_approval,
            include_code_analysis=include_code,
        )

    if launched and not query.strip():
        st.warning("Please enter a research question before launching.")

    return None
