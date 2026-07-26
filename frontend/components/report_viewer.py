"""
Nexus Research Platform — Report Viewer Component
Renders the final research report with TOC, citations, and export controls.
"""

import streamlit as st
from typing import Any
import re


def _count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _extract_headings(markdown: str) -> list[dict]:
    """Pull h2/h3 headings from markdown for the TOC."""
    toc: list[dict] = []
    for line in markdown.split("\n"):
        stripped = line.strip()
        if stripped.startswith("### "):
            toc.append({"level": 3, "text": stripped[4:].strip()})
        elif stripped.startswith("## "):
            toc.append({"level": 2, "text": stripped[3:].strip()})
    return toc


def _quality_badge(score: float) -> str:
    """Return an HTML badge coloured by quality score (0-10)."""
    if score >= 8:
        color, bg = "#00E676", "rgba(0,230,118,0.10)"
        label = "Excellent"
    elif score >= 6:
        color, bg = "#FF9800", "rgba(255,152,0,0.10)"
        label = "Good"
    elif score >= 4:
        color, bg = "#FFC107", "rgba(255,193,7,0.10)"
        label = "Fair"
    else:
        color, bg = "#FF5252", "rgba(255,82,82,0.10)"
        label = "Needs Work"

    return f"""
    <div style="
        display:inline-flex; align-items:center; gap:0.5rem;
        padding:0.35rem 0.9rem;
        background:{bg}; border:1px solid {color}40;
        border-radius:8px;
    ">
        <span style="
            font-family:'Inter',sans-serif; font-size:1.3rem; font-weight:800;
            color:{color};
        ">{score:.1f}</span>
        <span style="
            font-family:'Inter',sans-serif; font-size:0.7rem; font-weight:600;
            color:{color}; text-transform:uppercase; letter-spacing:1px;
        ">{label}</span>
    </div>
    """


def render_report(report_data: dict) -> None:
    """
    Render the final research report.

    Expected *report_data* shape::

        {
            "title": "...",
            "markdown": "...",
            "quality_score": 8.5,
            "citations": [{"id": 1, "text": "...", "url": "..."}],
            "metadata": {"word_count": 2340, "sections": 5},
        }
    """

    markdown_content: str = report_data.get("markdown", "")
    title: str = report_data.get("title", "Research Report")
    quality_score: float = report_data.get("quality_score", 0.0)
    citations: list = report_data.get("citations", [])
    metadata: dict = report_data.get("metadata", {})

    word_count = metadata.get("word_count", _count_words(markdown_content))
    headings = _extract_headings(markdown_content)

    # ── inject report styles ────────────────────────────────────────
    st.markdown(
        """
        <style>
            .report-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 1rem;
                margin-bottom: 1.2rem;
            }
            .report-title {
                font-family: 'Inter', sans-serif;
                font-weight: 800;
                font-size: 1.5rem;
                color: #E0E0E0;
                margin: 0;
            }
            .report-meta-row {
                display: flex;
                gap: 1rem;
                flex-wrap: wrap;
                margin-bottom: 1.2rem;
            }
            .meta-chip {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.3rem 0.75rem;
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                font-family: 'Inter', sans-serif;
                font-size: 0.72rem;
                color: rgba(224,224,224,0.6);
            }
            .meta-chip strong { color: #E0E0E0; font-weight: 700; }

            .report-body {
                background: linear-gradient(145deg, rgba(26,31,46,0.6) 0%, rgba(14,17,23,0.8) 100%);
                border: 1px solid rgba(108,99,255,0.1);
                border-radius: 16px;
                padding: 2rem 2.2rem;
                backdrop-filter: blur(12px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                line-height: 1.75;
                font-family: 'Inter', sans-serif;
                font-size: 0.92rem;
                color: rgba(224,224,224,0.85);
            }
            .report-body h1, .report-body h2, .report-body h3 { color: #E0E0E0; }
            .report-body h2 { border-bottom: 1px solid rgba(108,99,255,0.15); padding-bottom: 0.4rem; }
            .report-body a { color: #6C63FF; text-decoration: none; }
            .report-body a:hover { text-decoration: underline; }
            .report-body code {
                background: rgba(108,99,255,0.08);
                padding: 0.15rem 0.4rem;
                border-radius: 4px;
                font-size: 0.85em;
                color: #A78BFA;
            }
            .report-body blockquote {
                border-left: 3px solid #6C63FF;
                margin-left: 0;
                padding-left: 1rem;
                color: rgba(224,224,224,0.6);
                font-style: italic;
            }

            .toc-container {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
                padding: 1rem 1.2rem;
                margin-bottom: 1rem;
            }
            .toc-title {
                font-family: 'Inter', sans-serif;
                font-weight: 700;
                font-size: 0.82rem;
                color: rgba(224,224,224,0.5);
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 0.6rem;
            }
            .toc-item {
                font-family: 'Inter', sans-serif;
                font-size: 0.78rem;
                color: rgba(224,224,224,0.55);
                padding: 0.2rem 0;
                cursor: pointer;
                transition: color 0.2s;
            }
            .toc-item:hover { color: #6C63FF; }
            .toc-indent { padding-left: 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── report header ───────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="report-header">
            <h2 class="report-title">📄 {title}</h2>
            {_quality_badge(quality_score)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── meta chips ──────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="report-meta-row">
            <span class="meta-chip">📝 <strong>{word_count:,}</strong> words</span>
            <span class="meta-chip">📚 <strong>{len(citations)}</strong> citations</span>
            <span class="meta-chip">📑 <strong>{len(headings)}</strong> sections</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── layout: sidebar TOC + body ──────────────────────────────────
    toc_col, body_col = st.columns([1, 3])

    with toc_col:
        if headings:
            toc_html = '<div class="toc-container"><div class="toc-title">Contents</div>'
            for h in headings:
                indent_cls = "toc-indent" if h["level"] == 3 else ""
                prefix = "•" if h["level"] == 3 else "■"
                toc_html += f'<div class="toc-item {indent_cls}">{prefix} {h["text"]}</div>'
            toc_html += "</div>"
            st.markdown(toc_html, unsafe_allow_html=True)

    with body_col:
        st.markdown(
            f'<div class="report-body">{_md_to_safe_html(markdown_content)}</div>',
            unsafe_allow_html=True,
        )
        # Also render via st.markdown for proper markdown features
        with st.expander("📖 View Raw Markdown", expanded=False):
            st.markdown(markdown_content)

    # ── export buttons ──────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        st.download_button(
            "⬇️  Export Markdown",
            data=markdown_content,
            file_name=f"{_slug(title)}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with btn_col2:
        if st.button("📋  Copy to Clipboard", use_container_width=True):
            st.toast("Report copied to clipboard!", icon="✅")
            st.markdown(
                f"""
                <script>
                    navigator.clipboard.writeText({repr(markdown_content)});
                </script>
                """,
                unsafe_allow_html=True,
            )
    with btn_col3:
        citation_text = "\n".join(
            f"[{c.get('id', i+1)}] {c.get('text', '')} — {c.get('url', '')}"
            for i, c in enumerate(citations)
        )
        st.download_button(
            "📚  Export Citations",
            data=citation_text,
            file_name=f"{_slug(title)}_citations.txt",
            mime="text/plain",
            use_container_width=True,
        )


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60]


def _md_to_safe_html(md: str) -> str:
    """
    Minimal markdown → HTML for inline rendering.
    Streamlit's own markdown renderer handles the heavy lifting
    in the expandable section; this is for the styled card.
    """
    import html as html_mod

    text = html_mod.escape(md)
    # headings
    text = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.+)$", r"<h2>\1</h2>", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.+)$", r"<h1>\1</h1>", text, flags=re.MULTILINE)
    # bold / italic
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # links
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank">\1</a>', text)
    # line breaks
    text = text.replace("\n\n", "</p><p>").replace("\n", "<br/>")
    return f"<p>{text}</p>"
