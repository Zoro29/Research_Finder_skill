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
