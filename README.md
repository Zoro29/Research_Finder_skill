# Research Finder / `research-agent` skill

Research Finder is a deterministic scholarly search and evidence-aware
analysis project packaged with a self-contained [Agent Skills](https://agentskills.io/specification)
skill in [`research-agent/`](research-agent). It searches the
[OpenAlex](https://openalex.org/) catalogue, preserves combined constraints,
and optionally uses a local Ollama model for analysis. Agent Skills support
depends on the host agent and its available Python, network, and model tools;
creating `SKILL.md` does not grant those capabilities automatically.

## Skill layout

```text
research-agent/
├── SKILL.md
├── scripts/
│   ├── research.py
│   └── validate_skill.py
├── references/
└── assets/templates/
```

The Python implementation remains in the existing top-level
[`research_finder/`](research_finder) package so the refactor does not create
competing implementations.

## Install and use

```bash
python -m pip install -e .
research-agent search "RESEARCH - XD Large Language Models XY 2020-2024 XT Article"
```

On Ubuntu with an externally managed Python installation, use a virtual
environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

The skill script can also be run directly from the repository root without
installing the package:

```bash
python3 research-agent/scripts/research.py search "RESEARCH - XD Robotics"
```

Set `OPENALEX_MAILTO` (see `.env.example`) to provide OpenAlex a contact
address. Results are ranked by query-term matches, citations, and open access;
duplicate works are removed deterministically. The client never fabricates
papers when the service is unavailable.

## Python API

```python
from research_finder import parse_query
from research_finder.openalex import OpenAlexClient
results = OpenAlexClient().search(parse_query("RESEARCH - XD Climate Change XY 2022 XT Article"))
```

The grammar supports domains (`XD`), professors (`XP`), universities (`XU`),
year ranges (`XY`), and supported paper types (`XT`). A standalone `X` inside
`XD` separates concepts, so `XD Robotics X Machine Learning` means two
alternative domain terms. Components can appear in any order. Every parsed
request retains its `original_query`.

Different component categories constrain the same result set. Multiple
domains are OR/relevance alternatives. A no-result response keeps the
constraints visible rather than returning unrelated papers.

## Ollama

OpenAlex search works without Ollama. The optional adapter uses the local
Ollama HTTP API. Configure it with the exact tag returned by `ollama list`:

```bash
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=your-installed-tag
```

Publishing this skill does not distribute Gemma 4, install Ollama, or grant a
host agent access to the local machine. A compatible host agent may use its
own model to follow `SKILL.md`; explicit Python analysis sends requests to the
configured Ollama server. No model is downloaded automatically.

```bash
research-agent analyze "RESEARCH - XD Robotics"
research-agent outreach "RESEARCH - XP Professor Name" --professor "Professor Name"
research-agent related "adaptive soft robotic manipulation"
```

The `related` command performs a small preliminary OpenAlex overlap search; it
does not establish novelty or replace a systematic literature review.

## Validation and tests

Run the project tests:

```bash
python3 -m unittest discover -s tests -v
```

Run the dependency-light structural skill check:

```bash
python3 research-agent/scripts/validate_skill.py
```

If `skills-ref` is installed, the official validator target is:

```bash
skills-ref validate ./research-agent
```

The current implementation does not require third-party runtime dependencies.

## Limitations

OpenAlex author and institution matching is metadata-based and cannot always
resolve name collisions. Full-text retrieval and section-level extraction are
not yet automatic. Ollama structured generation, advanced author
disambiguation, and comprehensive novelty assessment remain optional future
work.
