from __future__ import annotations
import argparse, os, sys
from .query import parse_query, QueryParseError
from .openalex import OpenAlexClient, OpenAlexError
def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="research-agent", description="Search OpenAlex scholarly works")
    sub = p.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--mailto", default=os.getenv("OPENALEX_MAILTO"))
    args = p.parse_args(argv)
    try: q = parse_query(args.query); results = OpenAlexClient(args.mailto).search(q)
    except (QueryParseError, OpenAlexError, ValueError) as e: print(f"error: {e}", file=sys.stderr); return 2
    print(f"Domains: {', '.join(q.domains) or '(none)'}")
    print(f"Professors: {', '.join(q.professors) or '(none)'}")
    print(f"Universities: {', '.join(q.universities) or '(none)'}")
    print(f"Years: {q.year_range or '(any)'}; types: {', '.join(q.paper_types) or '(any)'}")
    if not results:
        print("No papers matched all supplied constraints.")
        return 0
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.paper.title} — {r.paper.publication_year or 'n.d.'} "
              f"[{r.paper.cited_by_count} citations] {r.paper.url or ''}")
    print("Analysis: optional; configure Ollama to analyze retrieved evidence.")
    return 0
if __name__ == "__main__": raise SystemExit(main())
