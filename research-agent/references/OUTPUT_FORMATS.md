# Output formats

## Search result

Each result contains a normalized paper title, authors, publication year, DOI
when available, OpenAlex work ID, venue, abstract when available, open-access
status, landing/source URL, citation count, matched terms, and deterministic
ranking score. Results state the interpreted constraints and retain
`original_query`.

## Paper analysis

Use these headings: research problem, motivation, research gap, main
contribution, methodology, evaluation, reported results, explicit limitations,
author-stated future work, and research opportunities. Label each claim as
author-stated, evidence-based inference, or speculative proposal and identify
the evidence source. State when the analysis is abstract-only.

## Research extension

Return title, motivation, supporting evidence, research gap, research question,
hypothesis or exploratory status, methodology, datasets/baselines/metrics,
expected contribution, feasibility, related-work overlap, and confidence.
Never represent a proposal as an established result.

## Professor outreach

Return two specific observations, one focused question, one clearly labeled
proposal, a concise adaptable paragraph, and the supporting paper URL. Mark
the text as a draft and include only student background supplied by the user.
