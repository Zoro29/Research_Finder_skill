from __future__ import annotations
import argparse, os, sys
from dataclasses import replace
from .query import parse_query, QueryParseError
from .openalex import OpenAlexClient, OpenAlexError
from .config import Settings
from .ollama import OllamaAnalyzer, OllamaError
from .professor_outreach import draft_outreach
from .research_opportunities import ResearchExtension, check_overlap
from .paper_retrieval import PaperRetriever
from .interactive_session import ResearchSession

def _print_paper(result, number):
    paper = result.paper
    print(f"\nPaper {number}: {paper.title}")
    print(f"OpenAlex ID: {paper.id}")
    print(f"Authors: {', '.join(paper.authors) or '(unavailable)'}")
    print(f"Year: {paper.publication_year or '(unavailable)'}")
    print(f"Venue: {paper.venue or '(unavailable)'}")
    print(f"DOI: {paper.doi or '(unavailable)'}")
    print(f"Open access: {'yes' if paper.open_access else 'no/unknown'}")
    print(f"Source: {paper.url or '(unavailable)'}")
    print(f"Abstract: {paper.abstract or '(unavailable)'}")

def _interactive(results):
    print("\nInteractive exploration is retrieval-focused; full text is not fabricated.")
    while True:
        try:
            selection = input("Select paper number (or q to quit): ").strip()
        except EOFError:
            return
        if selection.casefold() in {"q", "quit", ""}:
            return
        try:
            number = int(selection)
            result = results[number - 1]
        except (ValueError, IndexError):
            print("Enter a paper number from the displayed results.")
            continue
        _print_paper(result, number)
        print("Follow-up analysis: use the host agent in online mode, or run "
              "`research-agent analyze` in local mode.")
def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="research-agent", description="Search OpenAlex scholarly works")
    sub = p.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--mailto", default=os.getenv("OPENALEX_MAILTO"))
    interaction = search.add_mutually_exclusive_group()
    interaction.add_argument("--interactive", dest="interactive", action="store_true", default=True)
    interaction.add_argument("--no-interactive", dest="no_interactive", action="store_true")
    search.add_argument("--recent", action="store_true",
                        help="show newest matching papers first")
    search.add_argument("--limit", type=int, default=10,
                        help="maximum matching papers to retrieve (default: 10)")
    analyze = sub.add_parser("analyze", help="analyze evidence in the selected mode")
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
        if args.command == "search":
            if args.limit < 1 or args.limit > 200:
                raise ValueError("--limit must be between 1 and 200")
            q = replace(q, limit=args.limit)
        client = OpenAlexClient(getattr(args, "mailto", os.getenv("OPENALEX_MAILTO")))
        results = client.search(q, recent=getattr(args, "recent", False))
    except (QueryParseError, OpenAlexError, ValueError) as e: print(f"error: {e}", file=sys.stderr); return 2
    if args.command == "analyze":
        if not results:
            print("No paper matched all supplied constraints.", file=sys.stderr)
            return 1
        try:
            settings = Settings.from_env(load_dotenv=True)
            if settings.analysis_mode == "online":
                _print_paper(results[0], 1)
                print("\nOnline mode: the compatible host agent should analyze the evidence above "
                      "using its own model. This standalone CLI does not call a host-agent model.")
                return 0
            analysis = OllamaAnalyzer(
                settings.ollama_model, settings.ollama_base_url,
                timeout=settings.ollama_timeout,
                num_predict=settings.ollama_num_predict,
            ).analyze(
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
    results = results[:5]
    ordering = "newest first" if args.recent else "relevance-ranked"
    print(f"\nRESEARCH FINDER\nFound {len(results)} papers ({ordering}).")
    for i, r in enumerate(results, 1):
        paper = r.paper
        preview = paper.abstract[:300] + ("..." if len(paper.abstract) > 300 else "")
        print(f"\n[{i}] {paper.title}")
        print(f"    Authors: {', '.join(paper.authors) or '(unavailable)'}")
        print(f"    Year: {paper.publication_year or '(unavailable)'} | Venue: {paper.venue or '(unavailable)'} | Citations: {paper.cited_by_count}")
        print(f"    DOI: {paper.doi or '(unavailable)'}")
        print(f"    Abstract: {preview or '(unavailable)'}")
        print(f"    Open access: {'Yes' if paper.open_access else 'No/unknown'}")
        print(f"    URL: {paper.url or '(unavailable)'}")
    print("\nSelect a paper (1-5), enter a new search, or type q to quit.")
    interactive = not args.no_interactive
    if interactive:
        try:
            settings = Settings.from_env(load_dotenv=True)
            analyzer = None
            if settings.analysis_mode == "local":
                analyzer = OllamaAnalyzer(
                    settings.ollama_model, settings.ollama_base_url,
                    timeout=settings.ollama_timeout,
                    num_predict=settings.ollama_num_predict,
                )
            ResearchSession(results, PaperRetriever(), settings.analysis_mode, analyzer).run()
        except (OSError, ValueError) as exc:
            print(f"Interactive session unavailable: {exc}", file=sys.stderr)
    return 0
if __name__ == "__main__": raise SystemExit(main())
