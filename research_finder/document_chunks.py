"""Overlapping, section-aware chunks for bounded-context analysis."""
from __future__ import annotations
from dataclasses import dataclass
import re
from .paper_retrieval import RetrievedPaper

@dataclass(frozen=True)
class DocumentChunk:
    index: int
    text: str
    section: str | None = None

def chunk_document(document: RetrievedPaper, size: int = 6000, overlap: int = 600) -> tuple[DocumentChunk, ...]:
    if size <= overlap: raise ValueError("chunk size must exceed overlap")
    text = document.text.strip()
    if not text: return ()
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        fragment = text[start:end]
        section = next((heading for heading, body in document.sections if body.strip() and body.strip()[:80] in fragment), None)
        chunks.append(DocumentChunk(len(chunks), fragment, section))
        if end == len(text): break
        start = end - overlap
    return tuple(chunks)

def relevant_chunks(document: RetrievedPaper, question: str, limit: int = 4) -> tuple[DocumentChunk, ...]:
    chunks = chunk_document(document)
    terms = {term.casefold() for term in re.findall(r"\w{3,}", question)}
    ranked = sorted(chunks, key=lambda chunk: (-sum(term in chunk.text.casefold() for term in terms), chunk.index))
    return tuple(ranked[:limit])
