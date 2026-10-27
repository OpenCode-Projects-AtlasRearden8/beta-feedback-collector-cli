# STATUS.md — beta-feedback-collector-cli

Last updated: 2026-10-27
Owner: Asdale Dynamics, LLC (Dylan Asdale)
License: MIT (`LICENSE`)

## What was built

A dependency-free Python 3 CLI (`beta-reader`) for the beta-reader stage of a
book revision. It normalizes feedback sheets (CSV and Markdown, one per
reader), clusters recurring comments by chapter, separates nitpicks from
plot-level flags, and generates:

- `chapter-report.md` — per-chapter revision to-dos: consensus plot flags
  (multiple readers) first, then single-reader flags, contradictions to
  resolve, what readers loved (praise), and nitpicks
- `readers-summary.md` — reader-by-reader summary table plus per-reader
  details
- `contradictions.md` — reader-vs-reader disagreements on the same chapter
  (sentiment clashes like loved/hated, direction clashes like more/less)
- `revision-backlog.md` and `revision-backlog.csv` — prioritized sprint
  backlog: P0 consensus plot flags, P1 contradictions, P2 single plot flags,
  P3 nitpicks
- `normalized-feedback.csv` / `normalized-feedback.json` — the clean feed a
  downstream tool (e.g. book-bible-audit-cli) can consume

Plus an optional `brainstorm` subcommand that sends the plot-level flags to an
OpenAI-compatible endpoint (default: local Ollama `http://127.0.0.1:11434/v1`,
model `llama3.1`) and returns five theme/story ideas. No API key is ever
requested, stored, or sent.

Modules (src layout): `models`, `textutils`, `classify`, `normalize`,
`cluster`, `contradictions`, `report`, `readers`, `backlog`, `brainstorm`,
`cli`.

## How to run it

```bash
python3 -m pip install .        # provides the `beta-reader` command
beta-reader run --folder tests/fixtures --out demo-out
beta-reader report   --folder tests/fixtures
beta-reader summary  --folder tests/fixtures
beta-reader contradictions --folder tests/fixtures
beta-reader collect   --folder tests/fixtures
beta-reader brainstorm --folder tests/fixtures   # needs local Ollama running
```

Or without installing: `python3 -m betafeedback run --folder tests/fixtures`.

Flag forms honored in sheets: CSV `Type` column, Markdown/CSV inline tags
(`(plot)`, `(nitpick)`, `minor`, `major`), or keyword heuristics. Reader names
come from the file name, a CSV `Reader` column, or `--readers "stem=Name"`.

## Verification results

- `python3 -m pytest`: **39 passed** (Linux, Python 3.13) — covers
  normalization, chapter normalization, kind classification, clustering,
  contradictions, report/summary/backlog outputs, CLI end-to-end, and the
  offline-mocked brainstorm (success path, connection failure, malformed
  payload, keyless-by-design check).
- Editable pip install succeeded; console script `beta-reader --version`
  works (`0.1.0`).
- Full-pipeline smoke demo against `tests/fixtures`: wrote all 6 output files
  from 17 comments / 3 readers / 4 chapters, verified contents (consensus
  cluster for the slow opening across Ana+Ben, typo cluster across Ana+Ben,
  more/less backstory contradiction, loved/hated ending contradiction, praise
  bucket separate from nitpicks, P0..P3 ordering in the backlog).
- `brainstorm` verified offline via mocked HTTP; connection-failure path
  prints a friendly "is your local server running?" error.
- No third-party runtime dependencies; no network calls outside the optional
  brainstorm subcommand; no secrets or personal data in any file (fixtures are
  fictional).

## Known gaps

- Clustering is token-overlap heuristic: very different wordings of the same
  issue may not merge; unrelated short comments ("too dark", missing "the")
  could false-merge. Threshold is adjustable in `cluster.py`
  (`SIMILARITY_THRESHOLD`).
- Contradiction detection relies on sentiment word lists and antonym pairs,
  not a real NLP pass. Sarcasm and mixed sentences may slip through; it only
  compares readers (never a reader against themselves).
- `brainstorm` assumes a fast, plain-text chat completion response; streaming
  is not supported, and reasoning-heavy models may need `--timeout` raised.
- Non-CSV/Markdown formats (Google Docs exports, DOCX, plain email text) are
  not supported yet.
- Backlog task text truncation is not applied; very long comments make wide
  table rows.
- No `--chapter-filter` or verbose logging yet.
