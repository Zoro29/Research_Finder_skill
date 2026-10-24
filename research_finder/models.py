"""Typed, dependency-free data models used by Research Finder."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping

@dataclass(frozen=True)
class SearchQuery:
    text: str = ""
    domains: tuple[str, ...] = ()
    professors: tuple[str, ...] = ()
    universities: tuple[str, ...] = ()
    year_range: tuple[int, int] | None = None
    paper_types: tuple[str, ...] = ()
    limit: int = 10
    original_query: str = ""

    def __post_init__(self) -> None:
        if self.year_range is not None:
            if any(not 1500 <= y <= 2100 for y in self.year_range): raise ValueError("year_range is invalid")
            if self.year_range[0] > self.year_range[1]: raise ValueError("year range is reversed")
        if not 1 <= self.limit <= 200: raise ValueError("limit must be between 1 and 200")

    @property
    def year_from(self): return self.year_range[0] if self.year_range else None
    @property
    def year_to(self): return self.year_range[1] if self.year_range else None

@dataclass(frozen=True)
class Paper:
    id: str
    title: str
    authors: tuple[str, ...] = ()
    abstract: str = ""
    publication_year: int | None = None
    cited_by_count: int = 0
    doi: str | None = None
    venue: str | None = None
    open_access: bool = False
    url: str | None = None
    oa_pdf_url: str | None = None
    paper_type: str | None = None
    institutions: tuple[str, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, compare=False, repr=False)

    @classmethod
    def from_openalex(cls, item: Mapping[str, Any]) -> "Paper":
        authors = tuple(a.get("author", {}).get("display_name", "") for a in item.get("authorships", []) if a.get("author", {}).get("display_name"))
        institutions = tuple(i.get("display_name", "") for a in item.get("authorships", []) for i in a.get("institutions", []) if i.get("display_name"))
        primary = item.get("primary_location") or {}
        source = primary.get("source") or {}
        oa = item.get("open_access") or {}
        return cls(id=str(item.get("id") or item.get("doi") or ""),
                   title=str(item.get("title") or "Untitled"), authors=authors,
                   abstract=_abstract(item.get("abstract_inverted_index")),
                   publication_year=item.get("publication_year"),
                   cited_by_count=int(item.get("cited_by_count") or 0), doi=item.get("doi"),
                   venue=source.get("display_name"), open_access=bool(oa.get("is_oa")),
                   url=primary.get("landing_page_url") or item.get("id"),
                   oa_pdf_url=(
                       oa.get("oa_url") if isinstance(oa.get("oa_url"), str)
                       else (oa.get("oa_url") or {}).get("url")
                   ),
                   paper_type=item.get("type"), institutions=institutions, raw=item)

def _abstract(index: Any) -> str:
    if not isinstance(index, Mapping): return ""
    words: list[tuple[int, str]] = [(int(pos), word) for word, positions in index.items() if isinstance(positions, list) for pos in positions]
    return " ".join(word for _, word in sorted(words))

@dataclass(frozen=True)
class SearchResult:
    paper: Paper
    score: float
    matched_terms: tuple[str, ...] = ()
