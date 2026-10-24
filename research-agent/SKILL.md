---
name: research-agent
description: Discovers and analyzes academic papers, identifies research opportunities, searches research by domain and professor, and drafts evidence-grounded professor outreach. Use when exploring a research topic, investigating a professor's publications, reviewing academic literature, finding potential research directions, or preparing research outreach.
license: MIT
compatibility: Requires Python 3.11 or later and internet access for scholarly metadata retrieval. Ollama and a compatible local model are optional for AI-assisted paper analysis.
metadata:
  author: research-agent
  version: "1.0.0"
---

# Research Agent

Use this skill for academic discovery, paper analysis, evidence-based research
extensions, related-work checks, or professor outreach. It is explicitly
activated by commands beginning with `RESEARCH -`; the host agent may also use
it for ordinary natural-language research requests.

## Execution

From the skill root, run the executable implementation:

```bash
python scripts/research.py search "RESEARCH - XD Robotics XP Professor Name XY 2024-2026"
```

The script uses the existing `research_finder` package in the parent project
and does not require manual `PYTHONPATH` changes. Search does not require
Ollama. Configure `OPENALEX_MAILTO` when desired; configure Ollama only for
optional model-assisted analysis.

For supported model-dependent operations:

```bash
python scripts/research.py analyze "RESEARCH - XD Robotics"
python scripts/research.py outreach "RESEARCH - XP Professor Name" --professor "Professor Name"
python scripts/research.py related "adaptive soft robotic manipulation"
```

Set `LLM_PROVIDER=ollama`, `OLLAMA_BASE_URL`, and `OLLAMA_MODEL` to the exact
installed model tag before analysis. The skill never downloads models.

## Workflow

1. Parse and validate the request with the deterministic project parser.
2. Retrieve OpenAlex metadata and apply every supplied constraint to the same
   result set.
3. Deduplicate and rank results, retaining stable identifiers and source URLs.
4. Retrieve legitimate accessible text when analysis is requested; otherwise
   label the result abstract- or metadata-based.
5. Separate verified metadata, author-stated claims, evidence-based inferences,
   and speculative proposals.
6. Check proposed directions against related literature before discussing
   novelty.
7. Generate outreach only from identified paper evidence and mark it as a
   draft for user review.
8. Report uncertainty, unavailable evidence, filtering constraints, and
   network/model failures explicitly.

Read only the relevant reference when more detail is needed:

- `references/QUERY_SYNTAX.md`
- `references/RESEARCH_WORKFLOW.md`
- `references/OUTPUT_FORMATS.md`

Never invent papers, affiliations, results, citations, experiments, student
credentials, or novelty claims. A missing Ollama model must not block search.
