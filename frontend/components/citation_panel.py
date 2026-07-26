"""
Nexus Research Platform — Citation Panel Component
Displays citations with verification status, confidence bars, and coverage.
"""

import streamlit as st
from typing import Any


def render_citations(citations: list[dict], sources: list[dict] | None = None) -> None:
    """
    Render the citation verification panel.

    Expected shapes::

        citations = [
            {
                "id": 1,
                "text": "According to Smith et al. ...",
                "url": "https://...",
                "verified": True,
                "confidence": 0.92,
                "source_title": "Nature 2024",
            },
            ...
        ]

        sources = [
            {"url": "https://...", "title": "...", "snippet": "...", "relevance": 0.87},
            ...
        ]
    """

    if sources is None:
        sources = []

    total = len(citations) if citations else 0
    verified = sum(1 for c in citations if c.get("verified", False))
    coverage = (verified / total * 100) if total else 0

    # ── styles ──────────────────────────────────────────────────────
    st.markdown(
        """
        <style>
            .cite-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }
            .cite-title {
                font-family: 'Inter', sans-serif;
                font-weight: 700;
                font-size: 1.1rem;
                color: #E0E0E0;
            }
            .cite-coverage {
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                padding: 0.3rem 0.8rem;
                border-radius: 8px;
                font-family: 'Inter', sans-serif;
                font-size: 0.75rem;
                font-weight: 600;
            }
            .cite-card {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
                padding: 0.9rem 1rem;
                margin-bottom: 0.6rem;
                transition: border-color 0.25s;
            }
            .cite-card:hover {
                border-color: rgba(108,99,255,0.3);
            }
            .cite-card-top {
                display: flex;
                align-items: flex-start;
                gap: 0.6rem;
            }
            .cite-status-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 0.1rem; }
            .cite-text {
                font-family: 'Inter', sans-serif;
                font-size: 0.82rem;
                color: rgba(224,224,224,0.75);
                line-height: 1.5;
                flex: 1;
            }
            .cite-meta {
                display: flex;
                align-items: center;
                gap: 0.8rem;
                margin-top: 0.5rem;
                padding-left: 1.7rem;
            }
            .cite-url {
                font-family: 'Inter', sans-serif;
                font-size: 0.7rem;
                color: #6C63FF;
                text-decoration: none;
                word-break: break-all;
            }
            .cite-url:hover { text-decoration: underline; }
            .conf-bar-bg {
                flex: 0 0 80px;
                height: 6px;
                background: rgba(255,255,255,0.06);
                border-radius: 3px;
                overflow: hidden;
            }
            .conf-bar-fill { height: 100%; border-radius: 3px; }
            .conf-label {
                font-family: 'Inter', sans-serif;
                font-size: 0.65rem;
                color: rgba(224,224,224,0.4);
                min-width: 32px;
                text-align: right;
            }

            .source-card {
                background: rgba(0,0,0,0.15);
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 10px;
                padding: 0.75rem 1rem;
                margin-bottom: 0.5rem;
            }
            .source-title {
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                font-size: 0.82rem;
                color: #E0E0E0;
                margin-bottom: 0.2rem;
            }
            .source-snippet {
                font-family: 'Inter', sans-serif;
                font-size: 0.72rem;
                color: rgba(224,224,224,0.45);
                line-height: 1.45;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── header + coverage badge ─────────────────────────────────────
    if coverage >= 80:
        cov_color, cov_bg = "#00E676", "rgba(0,230,118,0.10)"
    elif coverage >= 50:
        cov_color, cov_bg = "#FF9800", "rgba(255,152,0,0.10)"
    else:
        cov_color, cov_bg = "#FF5252", "rgba(255,82,82,0.10)"

    st.markdown(
        f"""
        <div class="cite-header">
            <span class="cite-title">📚 Citations &amp; Sources</span>
            <span class="cite-coverage" style="background:{cov_bg};color:{cov_color};border:1px solid {cov_color}40;">
                ✓ {verified}/{total} verified · {coverage:.0f}% coverage
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── citation cards ──────────────────────────────────────────────
    if not citations:
        st.info("No citations available yet.")
        return

    for cite in citations:
        cid = cite.get("id", "?")
        text = cite.get("text", "")
        url = cite.get("url", "")
        verified = cite.get("verified", False)
        confidence = cite.get("confidence", 0.0)
        source_title = cite.get("source_title", "")

        icon = "✅" if verified else "❌"
        conf_pct = int(confidence * 100)

        if confidence >= 0.8:
            bar_color = "#00E676"
        elif confidence >= 0.5:
            bar_color = "#FF9800"
        else:
            bar_color = "#FF5252"

        card_html = f"""
        <div class="cite-card">
            <div class="cite-card-top">
                <span class="cite-status-icon">{icon}</span>
                <span class="cite-text">
                    <strong>[{cid}]</strong> {text}
                </span>
            </div>
            <div class="cite-meta">
                <a class="cite-url" href="{url}" target="_blank">
                    {source_title or url[:60]}
                </a>
                <div class="conf-bar-bg">
                    <div class="conf-bar-fill" style="width:{conf_pct}%;background:{bar_color};"></div>
                </div>
                <span class="conf-label">{conf_pct}%</span>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

    # ── expandable source details ───────────────────────────────────
    if sources:
        with st.expander(f"🔗 All Sources ({len(sources)})", expanded=False):
            for src in sources:
                title = src.get("title", "Untitled")
                snippet = src.get("snippet", "")
                url = src.get("url", "")
                relevance = src.get("relevance", 0)

                st.markdown(
                    f"""
                    <div class="source-card">
                        <div class="source-title">{title}</div>
                        <div class="source-snippet">{snippet[:200]}{'...' if len(snippet) > 200 else ''}</div>
                        <div style="margin-top:0.35rem;">
                            <a class="cite-url" href="{url}" target="_blank">{url[:80]}</a>
                            <span class="conf-label" style="margin-left:0.5rem;">
                                Relevance: {int(relevance * 100)}%
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
