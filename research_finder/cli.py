from __future__ import annotations
import argparse, os, sys
from .query import parse_query, QueryParseError
from .openalex import OpenAlexClient, OpenAlexError
from .config import Settings
from .ollama import OllamaAnalyzer, OllamaError
from .professor_outreach import draft_outreach
from .research_opportunities import ResearchExtension, check_overlap
def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="research-agent", description="Search OpenAlex scholarly works")
    sub = p.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--mailto", default=os.getenv("OPENALEX_MAILTO"))
    analyze = sub.add_parser("analyze", help="analyze the first matching paper with Ollama")
    analyze.add_argument("query")
    outreach = sub.add_parser("outreach", help="draft outreach from the first matching paper")
    outreach.add_argument("query")
    outreach.add_argument("--professor", required=True)
    related = sub.add_parser("related", help="run a preliminary related-work check")
    related.add_argument("proposal")
    args = p.parse_args(argv)
    try:
        if args.command == "related":
            q = parse_query("RESEARCH - XD " + args.proposal)
        else:
            q = parse_query(args.query)
        client = OpenAlexClient(getattr(args, "mailto", os.getenv("OPENALEX_MAILTO")))
        results = client.search(q)
    except (QueryParseError, OpenAlexError, ValueError) as e: print(f"error: {e}", file=sys.stderr); return 2
    if args.command == "analyze":
        if not results:
            print("No paper matched all supplied constraints.", file=sys.stderr)
            return 1
        try:
            settings = Settings.from_env()
            if settings.provider != "ollama":
                raise OllamaError("set LLM_PROVIDER=ollama and OLLAMA_MODEL to enable analysis")
            analysis = OllamaAnalyzer(settings.ollama_model, settings.ollama_base_url).analyze(
                [results[0].paper], "Summarize the research problem, method, findings, limitations, and evidence.")
        except (OllamaError, ValueError) as e:
            print(f"analysis unavailable: {e}", file=sys.stderr)
            return 3
        print(analysis.summary)
        return 0
    if args.command == "outreach":
        if not results:
            print("No paper matched all supplied constraints.", file=sys.stderr)
            return 1
        print(draft_outreach(results[0].paper, args.professor).paragraph)
        return 0
    if args.command == "related":
        extension = ResearchExtension(
            title=args.proposal, motivation="Preliminary related-work search.",
            research_question=args.proposal, hypothesis="Exploratory",
            methodology="Search OpenAlex metadata.", evidence=(),
        )
        checked = check_overlap(extension, lambda text: client.search(
            parse_query("RESEARCH - XD " + text)))
        print("Preliminary related work; this is not a novelty determination.")
        for result in checked.related_work:
            print(f"- {result.paper.title} {result.paper.url or ''}")
        return 0
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
