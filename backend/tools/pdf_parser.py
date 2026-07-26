"""PDF download and parsing tool using PyMuPDF (fitz)."""

from __future__ import annotations

import re
from typing import Optional

import fitz  # PyMuPDF
import httpx
import structlog

logger = structlog.get_logger(__name__)

# Defaults for chunking
_DEFAULT_CHUNK_SIZE = 4000  # characters
_DEFAULT_OVERLAP = 400


class PDFParserTool:
    """Downloads a PDF from a URL, extracts full text, and provides
    section-splitting and chunking utilities."""

    def __init__(
        self,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = _DEFAULT_OVERLAP,
        timeout: float = 30.0,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def parse_url(self, url: str) -> str:
        """Download a PDF from *url* and return its full text content.

        Raises
        ------
        httpx.HTTPStatusError
            If the HTTP response is not 2xx.
        RuntimeError
            If the PDF cannot be parsed.
        """
        logger.info("pdf_download_start", url=url)
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            pdf_bytes = response.content

        return self._extract_text(pdf_bytes, source_url=url)

    async def parse_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from raw PDF bytes."""
        return self._extract_text(pdf_bytes, source_url="<bytes>")

    async def extract_sections(self, text: str) -> list[dict[str, str]]:
        """Split *text* into logical sections based on common heading patterns.

        Returns a list of dicts with ``title`` and ``content`` keys.
        """
        # Attempt to split on lines that look like headings (ALL CAPS, numbered,
        # or short lines followed by longer paragraphs).
        heading_pattern = re.compile(
            r"^(?:"
            r"(?:#{1,4}\s+.+)"           # Markdown-style headings
            r"|(?:\d+\.[\d.]*\s+[A-Z].+)" # Numbered headings e.g. "1.2 Foo"
            r"|(?:[A-Z][A-Z\s]{4,60}$)"   # ALL-CAPS lines (likely headings)
            r")",
            re.MULTILINE,
        )

        headings = list(heading_pattern.finditer(text))

        if not headings:
            # No headings found — return entire text as a single section
            return [{"title": "Full Document", "content": text.strip()}]

        sections: list[dict[str, str]] = []
        for i, match in enumerate(headings):
            title = match.group().strip()
            start = match.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            content = text[start:end].strip()
            if content:
                sections.append({"title": title, "content": content})

        return sections

    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
    ) -> list[str]:
        """Split *text* into overlapping chunks for LLM consumption.

        Parameters
        ----------
        chunk_size:
            Max characters per chunk (default from constructor).
        overlap:
            Character overlap between consecutive chunks.
        """
        cs = chunk_size or self._chunk_size
        ov = overlap or self._chunk_overlap
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + cs
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start += cs - ov
        return chunks

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _extract_text(self, pdf_bytes: bytes, source_url: str) -> str:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as exc:
            logger.error("pdf_open_failed", source=source_url, error=str(exc))
            raise RuntimeError(f"Failed to open PDF from {source_url}: {exc}") from exc

        pages_text: list[str] = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text.strip():
                pages_text.append(page_text)

        doc.close()

        full_text = "\n\n".join(pages_text)
        logger.info(
            "pdf_parsed",
            source=source_url,
            pages=len(pages_text),
            chars=len(full_text),
        )
        return full_text
