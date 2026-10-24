"""Deterministic parser for the ``RESEARCH - XD/XP/XU/XY/XT`` grammar."""
from __future__ import annotations
import re
from .models import SearchQuery

class QueryParseError(ValueError): pass

SUPPORTED_TYPES = frozenset({
    "article", "book", "book-chapter", "dataset", "dissertation", "editorial",
    "erratum", "grant", "letter", "monograph", "peer-review", "preprint",
    "reference-entry", "report", "retraction", "review", "standard", "survey",
    "data-paper",
})
_MARKERS = {"XD": "domains", "XP": "professors", "XU": "universities",
            "XY": "year_range", "XT": "paper_types"}

def parse_query(value: str) -> SearchQuery:
    if not isinstance(value, str) or not value.strip(): raise QueryParseError("query cannot be empty")
    original = value.strip()
    if not re.match(r"^RESEARCH\s*-\s*", original, re.I):
        raise QueryParseError("query must start with 'RESEARCH - '")
    body = re.sub(r"^RESEARCH\s*-\s*", "", original, count=1, flags=re.I)
    matches = list(re.finditer(r"(?<!\w)(XD|XP|XU|XY|XT)(?!\w)", body, re.I))
    if not matches: raise QueryParseError("at least one XD, XP, XU, XY, or XT clause is required")
    if body[:matches[0].start()].strip(): raise QueryParseError("unexpected text before first clause")
    clauses = {}
    for i, match in enumerate(matches):
        key = match.group(1).upper()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        raw = body[match.end():end].strip().lstrip(":").strip().strip("-;").strip()
        if not raw: raise QueryParseError(f"{key} is missing a value")
        if key in clauses: raise QueryParseError(f"duplicate {key} clause")
        clauses[key] = raw
    values = {}
    for marker, raw in clauses.items():
        if marker == "XY":
            m = re.fullmatch(r"(15\d{2}|16\d{2}|17\d{2}|18\d{2}|19\d{2}|20\d{2}|21\d{2})(?:\s*[-:]\s*(\d{4}))?", raw)
            if not m: raise QueryParseError("XY must be a year or year range (YYYY-YYYY)")
            values["year_range"] = (int(m.group(1)), int(m.group(2) or m.group(1)))
        elif marker == "XT":
            types = [item.casefold() for item in _list(raw)]
            bad = [x for x in types if x not in SUPPORTED_TYPES]
            if bad: raise QueryParseError(f"unsupported paper type: {bad[0]}")
            values["paper_types"] = tuple(types)
        else:
            items = _list(raw)
            if marker == "XD":
                expanded = []
                for item in items:
                    expanded.extend(_split_domain_separator(item))
                items = expanded
            values[_MARKERS[marker]] = tuple(items)
    domains = values.get("domains", ())
    try:
        return SearchQuery(text=" ".join(domains), domains=domains,
        professors=values.get("professors", ()), universities=values.get("universities", ()),
        year_range=values.get("year_range"), paper_types=values.get("paper_types", ()),
        original_query=original)
    except ValueError as e:
        raise QueryParseError(str(e)) from e

def _list(raw: str) -> list[str]:
    items = [re.sub(r"\s+", " ", x).strip() for x in re.split(r"[,|]", raw)]
    if any(not x for x in items): raise QueryParseError("list contains a missing value")
    return items

def _split_domain_separator(value: str) -> list[str]:
    """Split only a whitespace-delimited standalone ``X`` token."""
    parts = re.split(r"(?<!\S)X(?!\S)", value, flags=re.IGNORECASE)
    result = [re.sub(r"\s+", " ", part).strip() for part in parts]
    if any(not part for part in result):
        raise QueryParseError("standalone X must separate two domain values")
    return result
