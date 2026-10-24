"""Evidence-aware extension and overlap-check interfaces.

Ideas are deliberately not invented by the deterministic fallback. Callers can
provide an LLM-generated proposal and a scholarly search callback, then retain
the related-work evidence alongside it.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Callable, Sequence
from .models import Paper, SearchResult

@dataclass(frozen=True)
class ResearchExtension:
    title: str
    motivation: str
    research_question: str
    hypothesis: str
    methodology: str
    evidence: tuple[str, ...]
    related_work: tuple[SearchResult, ...] = ()
    confidence: str = "uncertain"

def check_overlap(
    extension: ResearchExtension,
    search: Callable[[str], Sequence[SearchResult]],
) -> ResearchExtension:
    """Attach search-backed related work; never claim novelty from an empty result."""
    queries = (extension.title, extension.research_question)
    related = tuple(
        result
        for query in queries
        for result in search(query)
    )
    unique = {}
    for result in related:
        unique[result.paper.doi or result.paper.id] = result
    related = tuple(unique.values())
    return ResearchExtension(
        title=extension.title, motivation=extension.motivation,
        research_question=extension.research_question, hypothesis=extension.hypothesis,
        methodology=extension.methodology, evidence=extension.evidence,
        related_work=related,
        confidence="requires literature review" if related else "not established",
    )

def extractable_evidence(paper: Paper) -> tuple[str, ...]:
    """Return only facts directly available in normalized metadata."""
    evidence = [f"Title: {paper.title}"]
    if paper.abstract:
        evidence.append(f"Abstract: {paper.abstract}")
    if paper.url:
        evidence.append(f"Source: {paper.url}")
    return tuple(evidence)
