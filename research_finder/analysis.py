"""Interfaces for optional evidence-aware analysis; no model is required."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Sequence
from .models import Paper

@dataclass(frozen=True)
class Analysis:
    summary: str
    evidence: tuple[str, ...]
    limitations: tuple[str, ...] = ()

class Analyzer(Protocol):
    def analyze(self, papers: Sequence[Paper], question: str) -> Analysis: ...

class ExtractiveAnalyzer:
    def analyze(self, papers: Sequence[Paper], question: str) -> Analysis:
        evidence = tuple(f"{p.title} ({p.publication_year or 'n.d.'}; {p.cited_by_count} citations)" for p in papers[:5])
        return Analysis(f"Found {len(papers)} papers relevant to: {question}", evidence, ("This is an extractive overview, not a systematic review.",))
