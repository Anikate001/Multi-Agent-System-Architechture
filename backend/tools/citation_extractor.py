"""Citation extraction, verification, and hallucination detection tool."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Optional

import structlog

from schemas.research import Citation, Source

logger = structlog.get_logger(__name__)


class CitationExtractor:
    """Extracts inline citations from report text, verifies them against
    known sources, and detects potential hallucinations."""

    def __init__(self, similarity_threshold: float = 0.35) -> None:
        self._sim_threshold = similarity_threshold

    # ------------------------------------------------------------------
    # Extract
    # ------------------------------------------------------------------

    async def extract_citations(
        self,
        text: str,
        sources: list[Source],
    ) -> list[Citation]:
        """Find ``[Source N]`` markers in *text* and match them to *sources*.

        Returns a list of :class:`Citation` objects with confidence scores
        based on textual similarity between the surrounding claim and the
        source snippet.
        """
        pattern = re.compile(r"\[Source\s*(\d+)\]")
        citations: list[Citation] = []
        seen_claims: set[str] = set()

        for match in pattern.finditer(text):
            idx = int(match.group(1)) - 1  # 1-indexed → 0-indexed
            if idx < 0 or idx >= len(sources):
                logger.warning("citation_index_out_of_range", index=idx + 1)
                continue

            source = sources[idx]

            # Extract surrounding sentence as the "claim"
            claim = self._extract_surrounding_sentence(text, match.start())
            if claim in seen_claims:
                continue
            seen_claims.add(claim)

            confidence = self._compute_similarity(claim, source.snippet)
            citations.append(
                Citation(
                    claim=claim,
                    source_url=source.url,
                    source_title=source.title,
                    confidence=round(confidence, 3),
                    verified=False,
                )
            )

        logger.info("citations_extracted", count=len(citations))
        return citations

    # ------------------------------------------------------------------
    # Verify
    # ------------------------------------------------------------------

    async def verify_citation(self, citation: Citation, source_snippet: str = "") -> Citation:
        """Verify a single citation by comparing the claim against the source
        content.  Updates ``verified`` and ``confidence`` in-place and returns
        the updated citation.
        """
        if source_snippet:
            sim = self._compute_similarity(citation.claim, source_snippet)
            citation.confidence = round(sim, 3)
        citation.verified = citation.confidence >= self._sim_threshold
        return citation

    async def verify_all(
        self,
        citations: list[Citation],
        sources: list[Source],
    ) -> list[Citation]:
        """Batch-verify all citations against the source list."""
        source_map: dict[str, str] = {s.url: s.snippet for s in sources}
        verified: list[Citation] = []
        for c in citations:
            snippet = source_map.get(c.source_url, "")
            verified.append(await self.verify_citation(c, snippet))
        return verified

    # ------------------------------------------------------------------
    # Hallucination check
    # ------------------------------------------------------------------

    async def check_hallucinations(
        self,
        report: str,
        sources: list[Source],
    ) -> list[dict[str, str]]:
        """Identify factual-looking sentences in *report* that lack any
        citation and cannot be matched to any source.

        Returns a list of dicts with ``sentence`` and ``issue`` keys.
        """
        hallucinations: list[dict[str, str]] = []
        sentences = self._split_sentences(report)
        cited_pattern = re.compile(r"\[Source\s*\d+\]")

        for sentence in sentences:
            # Skip short or non-factual sentences
            if len(sentence.split()) < 8:
                continue
            # Skip sentences that already have a citation
            if cited_pattern.search(sentence):
                continue
            # Check if the sentence matches any source snippet
            best_sim = 0.0
            for source in sources:
                sim = self._compute_similarity(sentence, source.snippet)
                best_sim = max(best_sim, sim)
            if best_sim < self._sim_threshold:
                hallucinations.append(
                    {
                        "sentence": sentence.strip(),
                        "issue": "unsupported_claim",
                        "best_similarity": round(best_sim, 3),
                    }
                )

        logger.info("hallucination_check_complete", flagged=len(hallucinations))
        return hallucinations

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_surrounding_sentence(text: str, position: int) -> str:
        """Extract the sentence surrounding *position*."""
        # Walk backwards to find sentence start
        start = position
        while start > 0 and text[start - 1] not in ".!?\n":
            start -= 1
        # Walk forwards to find sentence end
        end = position
        while end < len(text) and text[end] not in ".!?\n":
            end += 1
        return text[start:end].strip()

    @staticmethod
    def _compute_similarity(a: str, b: str) -> float:
        """Return a 0-1 similarity score using SequenceMatcher."""
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Naïve sentence splitter."""
        raw = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in raw if s.strip()]
