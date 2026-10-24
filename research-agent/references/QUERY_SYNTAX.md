# Query syntax

Every typed query begins with `RESEARCH -` (case-insensitive). Components may
appear in any order:

| Marker | Meaning | Example |
| --- | --- | --- |
| `XD` | research domains/topics | `XD Soft Robotics X Manipulation` |
| `XP` | professor/researcher/author | `XP Jane Doe` |
| `XU` | university/institution | `XU Tsinghua University` |
| `XY` | year or inclusive year range | `XY 2024-2026` |
| `XT` | OpenAlex publication type | `XT Survey` |

`X` is a separator only when it is a standalone token inside `XD`; words such
as `Xylophone` are not split. Multiple domains are OR/relevance alternatives.
Different categories are AND constraints on the same papers. Names and phrases
remain multiword values until the next typed marker.

Examples:

```text
RESEARCH - XD Robotics
RESEARCH - XD Robotics X Machine Learning XP Professor Name
RESEARCH - XD Robotics XP Professor Name XU Tsinghua University XY 2024-2026 XT Survey
```

The parser rejects missing values, reversed or invalid years, unsupported
publication types, duplicate components, unexpected standalone `X`, and
queries without a typed component. It preserves the trimmed input as
`original_query`. Use `python scripts/research.py --help` for execution help.
