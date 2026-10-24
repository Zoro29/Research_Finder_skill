"""OpenAlex HTTP client. Network access is isolated here for easy mocking."""
from __future__ import annotations
import json, time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from .models import Paper, SearchQuery, SearchResult

class OpenAlexError(RuntimeError): pass
class OpenAlexClient:
    base_url = "https://api.openalex.org/works"
    def __init__(self, mailto: str | None = None, timeout: float = 15, opener=None):
        self.mailto, self.timeout, self.opener = mailto, timeout, opener or urlopen
    def fetch(self, query: SearchQuery) -> list[Paper]:
        search_terms = list(query.domains) + list(query.professors) + list(query.universities)
        params: dict[str, str] = {"search": " ".join(search_terms), "per-page": str(min(query.limit * 5, 200)), "select": "id,title,authorships,abstract_inverted_index,publication_year,cited_by_count,doi,primary_location,open_access,type"}
        filters = []
        if query.year_from: filters.append(f"from_publication_date:{query.year_from}-01-01")
        if query.year_to: filters.append(f"to_publication_date:{query.year_to}-12-31")
        if query.paper_types:
            # OpenAlex uses ``review`` for the works commonly described as
            # surveys; keep the user-facing vocabulary while using its API vocabulary.
            api_types = ["review" if kind == "survey" else kind for kind in query.paper_types]
            filters.append("type:" + "|".join(api_types))
        if filters: params["filter"] = ",".join(filters)
        if self.mailto: params["mailto"] = self.mailto
        request = Request(self.base_url + "?" + urlencode(params), headers={"Accept": "application/json", "User-Agent": "research-finder/0.1"})
        try:
            with self.opener(request, timeout=self.timeout) as response: payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as e: raise OpenAlexError(f"OpenAlex returned HTTP {e.code}") from e
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as e: raise OpenAlexError(f"OpenAlex request failed: {e}") from e
        return [Paper.from_openalex(x) for x in payload.get("results", []) if isinstance(x, dict)]
    def search(self, query: SearchQuery) -> list[SearchResult]:
        papers = self.fetch(query)
        seen: set[str] = set(); results = []
        terms = tuple(dict.fromkeys(t.lower() for t in (list(query.domains) + list(query.professors) + list(query.universities)) if len(t) > 1))
        for paper in papers:
            key = (paper.doi or paper.id).lower().rstrip("/")
            if key in seen: continue
            seen.add(key)
            haystack = (paper.title + " " + paper.abstract + " " + " ".join(paper.authors)).lower()
            authors = " ".join(paper.authors).lower()
            institutions = " ".join(paper.institutions).lower()
            if query.professors and not all(any(term.lower() in author.lower() for author in paper.authors) for term in query.professors): continue
            if query.universities and not all(term.lower() in institutions for term in query.universities): continue
            if query.year_range and (paper.publication_year is None or not query.year_from <= paper.publication_year <= query.year_to): continue
            if query.paper_types:
                paper_type = "review" if paper.paper_type == "survey" else paper.paper_type
                expected = {"review" if kind == "survey" else kind for kind in query.paper_types}
                if paper_type not in expected: continue
            matched = tuple(t for t in terms if t in haystack)
            if query.domains and not any(domain.casefold() in haystack for domain in query.domains):
                continue
            score = len(matched) * 10 + min(paper.cited_by_count / 100, 10) + (1 if paper.open_access else 0)
            results.append(SearchResult(paper, score, matched))
        return sorted(results, key=lambda r: (-r.score, -(r.paper.publication_year or 0), r.paper.title.casefold()))[:query.limit]
