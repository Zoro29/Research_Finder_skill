# Research workflow

## Retrieval and identity

OpenAlex is the primary metadata source. Retrieval errors are reported rather
than replaced with fabricated results. Stable work IDs and DOIs are preferred
for deduplication. A matching author or institution string is only a candidate
identity signal; ambiguous identities and historical affiliations must be
reported for verification.

## Evidence and analysis

Prefer legitimate open-access full text, then the official abstract and
metadata. If only an abstract is available, label analysis as abstract-based.
Record source URLs and section/page/table references when available. Classify
claims as verified metadata, author-stated, evidence-based inference, or
speculative proposal.

When a paper is selected, the retrieval layer first tries an OpenAlex
open-access URL or landing page, caches extracted text locally, and falls back
explicitly to the abstract and metadata. PDF/HTML extraction and overlapping
chunks are bounded and may be incomplete; the interface reports
`full-text`, `abstract-only`, or `unavailable` rather than claiming full-text
reading when extraction fails. Cached full text remains associated with the
same paper ID and source URL.

Analysis has two explicit modes. In `local` mode, Python sends the retrieved
evidence to the configured Ollama model. In `online` mode, the host agent
retrieves evidence with the Python engine and performs reasoning with its own
model; there is no Python API for calling the host model. Never silently switch
between these modes.

## Opportunities and outreach

Research extensions should be tied to a limitation, result, method, or
future-work statement. Include a precise question, hypothesis when defensible,
method, dataset/setup, baselines, metrics, feasibility, and uncertainty.
Search related literature before discussing overlap; an empty search never
proves novelty. Outreach drafts must mention actual paper evidence and must not
invent student experience or personal interactions.

## Fallbacks

Search remains available without Ollama. Ollama failures affect only
model-assisted analysis and must be stated clearly. Network failures must
include an actionable error and must not produce success-shaped fake results.
