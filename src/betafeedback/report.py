"""Per-chapter revision to-do reports (Markdown)."""

from __future__ import annotations

from .contradictions import sentiment
from .models import NITPICK, PLOT


def _chapter_title(chapter_key: str) -> str:
    if chapter_key.startswith("chapter_"):
        return f"Chapter {int(chapter_key[len('chapter_'):])}"
    if chapter_key.startswith("other_"):
        return chapter_key[len("other_"):]
    return chapter_key


def is_praise(cluster, contradiction_texts) -> bool:
    """A cluster is pure praise when every comment is positive and none of
    its comments is part of a flagged contradiction."""
    texts = {item.text for item in cluster.items}
    if texts & contradiction_texts:
        return False
    return all(sentiment(item.text) == 1 for item in cluster.items)


def is_contested(cluster, contradictions) -> bool:
    """True when the cluster's own items form a contradiction pair; those
    are rendered in the 'Contradictions to resolve' section instead."""
    texts = {item.text for item in cluster.items}
    return any(ta in texts and tb in texts for _, ta, _, tb, _ in contradictions)


def cluster_line(cluster, bullet_style="- [ ]") -> str:
    readers = ", ".join(cluster.readers)
    lead = f"{bullet_style} **({cluster.kind}) ({readers})**"
    first = cluster.samples[0]
    if cluster.reader_count > 1:
        others = "; ".join(f"{r}: “{s}”" for r, s in _pair_reader_samples(cluster))
        return f"{lead} {first}" + (f" — {others}" if others else "")
    return f"{lead} {first}"


def _pair_reader_samples(cluster):
    pairs = []
    for item in cluster.items:
        if item.text != cluster.samples[0]:
            pairs.append((item.reader, item.text))
    return pairs


def chapter_report(items, clusters, contradictions) -> str:
    """Build a Markdown revision to-do report grouped by chapter."""
    lines = ["# Revision To-Dos (per chapter)", ""]
    chapters = sorted({item.chapter_key for item in items})
    clusters_by_chapter = {}
    for cluster in clusters:
        clusters_by_chapter.setdefault(cluster.chapter_key, []).append(cluster)

    contradiction_texts = set()
    for _, ta, _, tb, _ in contradictions:
        contradiction_texts.add(ta)
        contradiction_texts.add(tb)

    for chapter_key in chapters:
        lines.append(f"## {_chapter_title(chapter_key)}")
        lines.append("")
        chapter_clusters = [
            c for c in clusters_by_chapter.get(chapter_key, [])
            if not is_contested(c, contradictions) and not is_praise(c, contradiction_texts)
        ]
        consensus = [c for c in chapter_clusters if c.reader_count > 1 and c.kind == PLOT]
        plot_singles = [c for c in chapter_clusters if c.reader_count == 1 and c.kind == PLOT]
        nitpick_clusters = [c for c in chapter_clusters if c.kind == NITPICK]
        praise = [c for c in clusters_by_chapter.get(chapter_key, []) if is_praise(c, contradiction_texts)]

        if consensus:
            lines.append("### Plot-level flags (multiple readers)")
            lines.extend(cluster_line(c) for c in consensus)
            lines.append("")
        if plot_singles:
            lines.append("### Plot-level flags (single reader)")
            lines.extend(cluster_line(c) for c in plot_singles)
            lines.append("")
        chapter_contradictions = [entry for entry in contradictions if entry[4] == chapter_key]
        if chapter_contradictions:
            lines.append("### Contradictions to resolve")
            for ra, ta, rb, tb, _ in chapter_contradictions:
                lines.append(f"- [ ] **{ra} vs {rb}:** “{ta}” vs “{tb}”")
            lines.append("")
        if praise:
            lines.append("### What readers loved (keep this)")
            lines.extend(cluster_line(c, "- [x]") for c in praise)
            lines.append("")
        if nitpick_clusters:
            lines.append("### Nitpicks")
            lines.extend(cluster_line(c) for c in nitpick_clusters)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
