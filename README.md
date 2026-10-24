Required changes -- Improving latency of the model
                 -- Improving overall Architecture Design 


Have you struggled like me, Reading multiple research paper before mailing a proffesor for a junior research internship, finding papers related to your Domains, and  Going through full paper when someone ask you something simple :(
I made a solution for the same - Research_finder -> It finds, reads and answers your question.
find research papers using filters - Multiple Domains, Multiple Profesors

But isn't this idea too simple ?? 

I felt it too, but we will be using this same skill and upgrade it to something more important.
Sometimes you might come to challenges/ hackathons (especiallly Kaggle) where just knowing the code is not enough you need High-level knowlege in chemistry , physics etc.
Here we are feeding our agents with knowlege from Research Papers by top Researchers in their field. :)

lets take a example to understand better, 

     let there be a kaggle ml-competition to detect cells.
     our agent can use our skill find the best recent paper about detecting cells / image processing . 
     Now our agent has high level knowlege to work on our ML model.






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
python3 -m pip install --user --break-system-packages -e .
research-agent search "RESEARCH - XD Large Language Models XY 2020-2024 XT Article"
```

The `--break-system-packages` flag is needed only on Ubuntu installations
using Python's PEP 668 externally-managed-environment protection. This project
has no third-party runtime dependencies. If you prefer an isolated install,
use a virtual environment and either activate it or call its executable:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
source .venv/bin/activate
```

If `research-agent` is still not found after a user install, ensure
`~/.local/bin` is on `PATH`, then start a new shell:

```bash
export PATH="$HOME/.local/bin:$PATH"
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

## Interactive paper research

Search displays up to five results by default and opens a paper session:

```bash
research-agent search "RESEARCH - XD robotics"
```

To prioritize the most recent matching papers while preserving all query
filters:

```bash
research-agent search --recent "RESEARCH - XD robotics XY 2020-2026"
```

Use `--limit N` to control the retrieval window. `--recent` sorts by
publication date first; without it, results use relevance, citation count,
and open-access signals.

Use `--no-interactive` for batch output. In a session, enter a paper number
first; selection only establishes the active paper and waits for your next
command. Use `summary`, `method`, `limitations`, `section`, `compare 2`,
`switch`, `back`, or natural-language questions. Selected papers are retrieved from
legitimate OpenAlex/landing-page sources and cached in `.research_cache/`.
If full text cannot be extracted, the session says that full text is
unavailable and limits analysis to the abstract and metadata.

## Ollama

OpenAlex search works without Ollama. The optional adapter uses the local
Ollama HTTP API. Configure it with the exact tag returned by `ollama list`:

```bash
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=your-installed-tag
```

Choose the analysis mode explicitly:

| Feature | Local Mode | Online Mode |
| --- | --- | --- |
| Paper discovery | OpenAlex | OpenAlex |
| Paper retrieval | Python research engine | Python research engine |
| Analysis model | Gemma 4 through Ollama | Compatible host agent's model |
| Requires Ollama | Yes | No |
| Requires internet for OpenAlex search | Yes | Yes |
| LLM inference per-token API fees | None for local inference | Depends on host service |
| Uses local hardware for inference | Yes | Not for the host model |
| Privacy | Evidence is sent to local Ollama; OpenAlex queries still go online | Depends on host agent and its data policies |
| Analysis quality | Depends on local model and available context | Depends on host model and available context |

For local mode:

```bash
export RESEARCH_ANALYSIS_MODE=local
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=gemma4:e2b
export OLLAMA_TIMEOUT=180
export OLLAMA_NUM_PREDICT=512
```

`OLLAMA_TIMEOUT` and `OLLAMA_NUM_PREDICT` are configurable because local
inference latency depends on hardware, model loading, and paper context.

For online mode:

```bash
export RESEARCH_ANALYSIS_MODE=online
```

Online mode does not call Ollama from Python. The compatible host agent must
execute retrieval, inspect the returned evidence, and perform the analysis
using its own model. This repository does not invent an API for accessing a
host agent's internal model. Local inference has no per-token API fee, but it
still consumes hardware and electricity. Online inference may require a paid
subscription, usage allowance, or API billing.

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
