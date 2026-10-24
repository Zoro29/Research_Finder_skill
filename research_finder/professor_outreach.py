"""Conservative, source-backed outreach draft generation."""
from __future__ import annotations
from dataclasses import dataclass
from .models import Paper

@dataclass(frozen=True)
class OutreachDraft:
    observations: tuple[str, ...]
    research_question: str
    proposed_extension: str
    paragraph: str
    source_url: str | None
    evidence_basis: str = "metadata/abstract-based draft; verify before sending"

def draft_outreach(paper: Paper, professor: str) -> OutreachDraft:
    """Create a reviewable draft without inventing student credentials or results."""
    basis = "the abstract" if paper.abstract else "the available metadata"
    observation = f"I read {paper.title}, focusing on {basis}."
    question = "What limitation or follow-up experiment do you consider most important for this work?"
    proposal = "Proposal: investigate a carefully defined extension supported by a broader related-work review."
    paragraph = (
        f"Dear {professor},\n\nI am interested in your paper “{paper.title}”. "
        f"Based on {basis}, I would like to understand which unresolved limitation "
        f"you would prioritize for follow-up. {proposal} I would appreciate your "
        f"view on whether this would be a useful direction.\n\n"
        "This is a draft for personalization and verification."
    )
    return OutreachDraft((observation,), question, proposal, paragraph, paper.url)
