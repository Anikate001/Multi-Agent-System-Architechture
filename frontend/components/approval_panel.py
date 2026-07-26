"""
Nexus Research Platform — Approval Panel Component
Human-in-the-loop gate for reviewing, approving, or rejecting agent output.
"""

import streamlit as st
from typing import Any


def render_approval_panel(
    task_id: str,
    review_data: dict,
    api_client: Any,
) -> str | None:
    """
    Render the human-approval gate.

    Returns:
        "approved"  — user clicked Approve
        "revised"   — user clicked Request Revision
        "rejected"  — user clicked Reject
        None        — no action taken this render

    Expected *review_data* shape::

        {
            "quality_score": 7.4,
            "summary": "The report covers ...",
            "strengths": ["Comprehensive sources", ...],
            "weaknesses": ["Missing quantitative data", ...],
            "suggestions": ["Add a comparison table", ...],
            "revision_count": 1,
        }
    """

    quality = review_data.get("quality_score", 0.0)
    summary = review_data.get("summary", "")
    strengths = review_data.get("strengths", [])
    weaknesses = review_data.get("weaknesses", [])
    suggestions = review_data.get("suggestions", [])
    rev_count = review_data.get("revision_count", 0)

    # ── quality colour ──────────────────────────────────────────────
    if quality >= 8:
        q_color, q_label = "#00E676", "Excellent"
    elif quality >= 6:
        q_color, q_label = "#FF9800", "Good"
    elif quality >= 4:
        q_color, q_label = "#FFC107", "Fair"
    else:
        q_color, q_label = "#FF5252", "Poor"

    # ── styles ──────────────────────────────────────────────────────
    st.markdown(
        """
        <style>
            .approval-card {
                background: linear-gradient(145deg, rgba(26,31,46,0.85) 0%, rgba(14,17,23,0.92) 100%);
                border: 1px solid rgba(108,99,255,0.2);
                border-radius: 16px;
                padding: 1.8rem 2rem;
                backdrop-filter: blur(16px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.05);
                margin-bottom: 1.5rem;
            }
            .approval-title {
                font-family: 'Inter', sans-serif;
                font-weight: 700;
                font-size: 1.15rem;
                color: #E0E0E0;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.3rem;
            }
            .approval-sub {
                font-family: 'Inter', sans-serif;
                font-size: 0.78rem;
                color: rgba(224,224,224,0.4);
                margin-bottom: 1rem;
            }
            .quality-ring {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1.2rem;
            }
            .quality-circle {
                width: 72px; height: 72px;
                border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                font-family: 'Inter', sans-serif;
                font-weight: 900; font-size: 1.4rem;
            }
            .quality-meta {
                font-family: 'Inter', sans-serif;
            }
            .quality-label {
                font-size: 0.95rem; font-weight: 700;
            }
            .quality-rev {
                font-size: 0.7rem; color: rgba(224,224,224,0.4);
            }
            .review-list {
                margin: 0.3rem 0 0.8rem 0;
                padding-left: 1.2rem;
            }
            .review-list li {
                font-family: 'Inter', sans-serif;
                font-size: 0.8rem;
                color: rgba(224,224,224,0.7);
                margin-bottom: 0.35rem;
                line-height: 1.45;
            }
            .section-label {
                font-family: 'Inter', sans-serif;
                font-weight: 600; font-size: 0.82rem;
                margin-bottom: 0.2rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── card ────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="approval-card">
            <div class="approval-title">🛡️ Human Review Required</div>
            <div class="approval-sub">
                The Critic agent has completed its review. Please evaluate and decide.
            </div>

            <div class="quality-ring">
                <div class="quality-circle" style="
                    background: {q_color}18;
                    border: 3px solid {q_color};
                    color: {q_color};
                    box-shadow: 0 0 20px {q_color}30;
                ">{quality:.1f}</div>
                <div class="quality-meta">
                    <div class="quality-label" style="color:{q_color};">{q_label}</div>
                    <div class="quality-rev">Revision #{rev_count} · Score out of 10</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── summary ─────────────────────────────────────────────────────
    if summary:
        st.markdown(
            f"""
            <div style="
                padding: 0.8rem 1rem;
                background: rgba(108,99,255,0.05);
                border-left: 3px solid #6C63FF;
                border-radius: 0 10px 10px 0;
                margin-bottom: 1rem;
                font-family: 'Inter', sans-serif;
                font-size: 0.82rem;
                color: rgba(224,224,224,0.7);
                line-height: 1.6;
            ">{summary}</div>
            """,
            unsafe_allow_html=True,
        )

    # ── strengths / weaknesses / suggestions ────────────────────────
    col_s, col_w = st.columns(2)

    with col_s:
        if strengths:
            st.markdown(
                '<p class="section-label" style="color:#00E676;">✅ Strengths</p>',
                unsafe_allow_html=True,
            )
            items = "".join(f"<li>{s}</li>" for s in strengths)
            st.markdown(f'<ul class="review-list">{items}</ul>', unsafe_allow_html=True)

    with col_w:
        if weaknesses:
            st.markdown(
                '<p class="section-label" style="color:#FF5252;">⚠️ Weaknesses</p>',
                unsafe_allow_html=True,
            )
            items = "".join(f"<li>{w}</li>" for w in weaknesses)
            st.markdown(f'<ul class="review-list">{items}</ul>', unsafe_allow_html=True)

    if suggestions:
        st.markdown(
            '<p class="section-label" style="color:#FF9800;">💡 Suggestions</p>',
            unsafe_allow_html=True,
        )
        items = "".join(f"<li>{s}</li>" for s in suggestions)
        st.markdown(f'<ul class="review-list">{items}</ul>', unsafe_allow_html=True)

    # ── action buttons ──────────────────────────────────────────────
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    feedback_text = st.text_area(
        "Revision feedback (optional — shown to Writer agent)",
        placeholder="e.g. Add more quantitative data and a comparison table in section 3...",
        height=80,
        key="approval_feedback",
    )

    st.markdown(
        """
        <style>
            div[data-testid="stHorizontalBlock"] .approve-btn button {
                background: linear-gradient(135deg, #00E676, #00C853) !important;
                color: #0E1117 !important; font-weight: 700 !important;
            }
            div[data-testid="stHorizontalBlock"] .revise-btn button {
                background: linear-gradient(135deg, #FF9800, #F57C00) !important;
                color: #0E1117 !important; font-weight: 700 !important;
            }
            div[data-testid="stHorizontalBlock"] .reject-btn button {
                background: linear-gradient(135deg, #FF5252, #D32F2F) !important;
                color: #fff !important; font-weight: 700 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    btn_a, btn_r, btn_x = st.columns(3)

    with btn_a:
        if st.button("✅  Approve", use_container_width=True, type="primary", key="btn_approve"):
            try:
                api_client.approve_task(task_id)
                st.success("Report approved and finalised!")
                return "approved"
            except RuntimeError as exc:
                st.error(str(exc))

    with btn_r:
        if st.button("🔄  Request Revision", use_container_width=True, key="btn_revise"):
            try:
                api_client.reject_task(task_id, feedback=feedback_text)
                st.info("Revision requested — agents are refining the report...")
                return "revised"
            except RuntimeError as exc:
                st.error(str(exc))

    with btn_x:
        if st.button("❌  Reject", use_container_width=True, key="btn_reject"):
            try:
                api_client.reject_task(task_id, feedback=feedback_text or "Report rejected by reviewer.")
                st.warning("Report rejected.")
                return "rejected"
            except RuntimeError as exc:
                st.error(str(exc))

    return None
