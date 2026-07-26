"""Markdown (and optional PDF) export for ResearchReport objects."""

from __future__ import annotations

from datetime import timezone
from typing import Optional

import structlog

from schemas.research import ResearchReport

logger = structlog.get_logger(__name__)


class MarkdownExporter:
    """Convert a :class:`ResearchReport` into formatted Markdown or PDF."""

    # ------------------------------------------------------------------
    # Markdown
    # ------------------------------------------------------------------

    def export_report(self, report: ResearchReport) -> str:
        """Render *report* as clean Markdown without inline citation references."""
        lines: list[str] = []

        # Title
        lines.append(f"# {report.title}")
        lines.append("")

        # Metadata
        generated = report.generated_at.strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"*Generated: {generated}*  ")
        lines.append(f"*Quality Score: {report.quality_score}/10*  ")
        lines.append(f"*Total Citations: {report.total_citations}*  ")
        lines.append("")

        # Abstract
        lines.append("## Abstract")
        lines.append("")
        lines.append(report.abstract)
        lines.append("")

        # Sections
        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")
            if section.word_count:
                lines.append(f"*({section.word_count} words)*")
                lines.append("")

        # Bibliography
        if report.bibliography:
            lines.append("## Bibliography")
            lines.append("")
            for i, source in enumerate(report.bibliography, 1):
                retrieved = source.retrieved_at.strftime("%Y-%m-%d")
                lines.append(
                    f"{i}. [{source.title}]({source.url}) — Retrieved {retrieved}"
                )
            lines.append("")

        return "\n".join(lines)

    def export_with_citations(self, report: ResearchReport) -> str:
        """Render *report* as Markdown with inline citations and a numbered
        bibliography at the end."""
        lines: list[str] = []

        lines.append(f"# {report.title}")
        lines.append("")

        generated = report.generated_at.strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"*Generated: {generated} | Quality: {report.quality_score}/10 | Citations: {report.total_citations}*")
        lines.append("")

        # Abstract
        lines.append("## Abstract")
        lines.append("")
        lines.append(report.abstract)
        lines.append("")

        # Sections with inline citations
        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

            # Per-section citation footnotes
            if section.citations:
                lines.append("**Citations in this section:**")
                lines.append("")
                for cit in section.citations:
                    verified_tag = "✅" if cit.verified else "⚠️"
                    lines.append(
                        f"- {verified_tag} *\"{cit.claim[:80]}...\"* — "
                        f"[{cit.source_title}]({cit.source_url}) "
                        f"(confidence: {cit.confidence:.0%})"
                    )
                lines.append("")

        # Full bibliography
        if report.bibliography:
            lines.append("---")
            lines.append("")
            lines.append("## References")
            lines.append("")
            for i, source in enumerate(report.bibliography, 1):
                retrieved = source.retrieved_at.strftime("%Y-%m-%d")
                lines.append(
                    f"[{i}] {source.title}. {source.url} "
                    f"(Retrieved {retrieved}). Relevance: {source.relevance_score:.0%}"
                )
            lines.append("")

        # Metadata
        if report.metadata:
            lines.append("---")
            lines.append("")
            lines.append("## Metadata")
            lines.append("")
            for key, value in report.metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # PDF (best-effort via markdown → HTML → PDF with fitz)
    # ------------------------------------------------------------------

    def export_pdf(self, report: ResearchReport) -> bytes:
        """Render *report* as a simple PDF.

        This uses PyMuPDF's ``Story`` API to convert HTML into PDF pages.
        If PyMuPDF is unavailable or the conversion fails, the Markdown
        text is embedded in a minimal PDF.
        """
        try:
            import fitz  # PyMuPDF

            md_text = self.export_with_citations(report)
            html = self._markdown_to_html(md_text)

            doc = fitz.open()
            page_rect = fitz.paper_rect("A4")
            margin = 50
            content_rect = fitz.Rect(
                margin, margin,
                page_rect.width - margin,
                page_rect.height - margin,
            )

            story = fitz.Story(html=html)
            more_pages = True
            while more_pages:
                page = doc.new_page(width=page_rect.width, height=page_rect.height)
                writer = story.place(content_rect)
                story.draw(page)
                more_pages = writer  # 0 means done

            pdf_bytes = doc.tobytes()
            doc.close()

            logger.info("pdf_exported", pages=doc.page_count if hasattr(doc, 'page_count') else "unknown")
            return pdf_bytes

        except Exception as exc:
            logger.warning("pdf_export_fallback", error=str(exc))
            # Fallback: create a minimal text-only PDF
            return self._fallback_pdf(report)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _markdown_to_html(md: str) -> str:
        """Very basic Markdown → HTML conversion for PDF rendering."""
        html_lines: list[str] = [
            "<html><body style='font-family: sans-serif; font-size: 11pt;'>"
        ]
        for line in md.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# "):
                html_lines.append(f"<h1>{stripped[2:]}</h1>")
            elif stripped.startswith("## "):
                html_lines.append(f"<h2>{stripped[3:]}</h2>")
            elif stripped.startswith("### "):
                html_lines.append(f"<h3>{stripped[4:]}</h3>")
            elif stripped.startswith("- "):
                html_lines.append(f"<li>{stripped[2:]}</li>")
            elif stripped.startswith("*") and stripped.endswith("*"):
                html_lines.append(f"<em>{stripped.strip('*')}</em><br/>")
            elif stripped == "---":
                html_lines.append("<hr/>")
            elif stripped:
                html_lines.append(f"<p>{stripped}</p>")
        html_lines.append("</body></html>")
        return "\n".join(html_lines)

    def _fallback_pdf(self, report: ResearchReport) -> bytes:
        """Produce a bare-minimum PDF containing the Markdown text."""
        import fitz

        doc = fitz.open()
        text = self.export_report(report)
        lines = text.split("\n")

        page = doc.new_page()
        y = 72
        for line in lines:
            if y > page.rect.height - 72:
                page = doc.new_page()
                y = 72
            page.insert_text((72, y), line[:100], fontsize=10)
            y += 14

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes
