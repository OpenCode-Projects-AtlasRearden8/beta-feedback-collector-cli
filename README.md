# beta-feedback-collector-cli

Normalize, cluster, and act on beta-reader feedback for a manuscript draft.
Point it at a folder of feedback sheets (CSV or Markdown, one per reader) and it
produces a per-chapter revision to-do report, a reader-by-reader summary,
contradiction highlights, and a prioritized revision sprint backlog.

Built for **Asdale Dynamics, LLC** — beginner-friendly AI education and practical
tools for authors. Plain English, step by step, never condescending.

## Why

Beta readers send feedback in every format imaginable: CSVs, bullet-point
emails, chapter notes. Before a revision sprint you need to know:

- **What three readers all said** (fix that first)
- **What only one reader said** (verify, then decide)
- **Where readers flat-out disagree** (a contraction needs a judgment call)
- What's just a **typo** versus a real **plot-level problem**
- What they **loved** (don't break it while fixing the rest)

## Install

Requires Python 3.9+. No third-party dependencies.

```bash
git clone https://github.com/dylanasdale/beta-feedback-collector-cli
cd beta-feedback-collector-cli
python3 -m pip install .
```

Or try it without installing:

```bash
python3 -m betafeedback run --folder feedback
```

## Feedback sheet formats

**CSV** — one file per reader (default). Needs `Chapter` and `Comment` columns;
optional `Element`, `Type`, `Reader` columns are honored.

```csv
Chapter,Element,Type,Comment
3,Ending,plot,The twist comes out of nowhere
3,Prose,nitpick,Comma splice on page 41
```

**Markdown** — one file per reader. Chapter headings (`## Chapter 1`) group the
bullets below them; each bullet is one comment.

```markdown
## Chapter 3

- (plot) The twist comes out of nowhere
- (Pacing) too slow before the midpoint
```

The reader's name comes from the file name (`reader_ana.csv` → `Ana`), a
`Reader` CSV column, or `--readers "stem=Name"`. Comment type is taken from the
`Type` column, an inline `(plot)`/`(nitpick)`/`minor`/`major` tag, or keyword
heuristics (typos/grammar/formatting → nitpick; pacing/ending/motivation/stakes
→ plot-level).

## Use

```bash
beta-reader run --folder feedback              # full pipeline, writes beta-feedback-out/
beta-reader collect --folder feedback          # normalized CSV + JSON only
beta-reader report --folder feedback           # per-chapter revision to-dos
beta-reader summary --folder feedback          # reader-by-reader summary
beta-reader contradictions --folder feedback   # where readers disagree
beta-reader brainstorm --folder feedback       # optional, needs a local LLM
```

Options: `--out DIR` (default `beta-feedback-out`), `--readers`, and for
`brainstorm`: `--base-url`, `--model`, `--timeout`.

### Outputs (from `run`)

| File | What it is |
|---|---|
| `chapter-report.md` | Revision to-dos per chapter: consensus flags, single-reader flags, contradictions, praise, nitpicks |
| `readers-summary.md` | Comment counts, chapters flagged, plot vs nitpick split per reader |
| `contradictions.md` | Reader-vs-reader disagreements on the same chapter (loved/hated, more/less, slow/self-contradicting pacing) |
| `revision-backlog.md` / `.csv` | Prioritized sprint backlog: P0 consensus plot flags → P1 contradictions → P2 single flags → P3 nitpicks |
| `normalized-feedback.csv` / `.json` | Clean, schema-stable feed for other tools |

### How clustering and contradiction detection work

Clustering recurs comments by chapter using token-overlap similarity
(stopword-filtered, tolerance for plurals/misspellings of the same word) —
comments that share roughly a third of their content tokens in the same chapter
are merged, and clusters spanning multiple readers become "consensus" items.
Contradictions pair comments from **different readers** in the **same chapter**
that share a topic but clash in sentiment (loved vs hated) or direction
(more vs less, slow vs rushed). It is deliberately heuristic — treat it as a
helpful first pass, not gospel.

## Optional: theme brainstorm with a local LLM

`beta-reader brainstorm` sends the plot-level flags to an OpenAI-compatible
endpoint and gets back five theme/story brainstorm ideas. Defaults to a local
Ollama server at `http://127.0.0.1:11434/v1` with model `llama3.1`:

```bash
ollama serve        # if it isn't already running
ollama pull llama3.1
beta-reader brainstorm --folder feedback
```

Different local server? `--base-url http://127.0.0.1:8080/v1 --model my-model`.
**No API key is ever requested, stored, or sent** — this tool is built for
keyless local endpoints, keeping your manuscript and your data on your machine.

## Development

```bash
python3 -m pip install -e .
python3 -m pytest
```

Sample feedback fixtures live in `tests/fixtures/` (three fictional readers
over four chapters) and double as format examples.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.

Companion tool: **book-bible-audit-cli** checks your manuscript against its
series bible; this tool processes what your beta readers say about it. Both
pairs well with the plain-English AI guides at [dylanasdale.github.io](https://dylanasdale.github.io).
