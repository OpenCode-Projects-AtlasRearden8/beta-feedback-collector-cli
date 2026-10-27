"""Cluster recurring comments within a chapter using token-overlap similarity."""

from __future__ import annotations

from .models import Cluster
from .textutils import content_tokens

SIMILARITY_THRESHOLD = 0.32


def similarity(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _ordered_chapter_keys(items) -> list:
    keys = sorted({item.chapter_key for item in items})
    return sorted(
        keys,
        key=lambda key: (not key.startswith("chapter_"), key),  # numbered chapters first
    )


def cluster_items(items) -> list:
    clusters = []
    by_chapter = {}
    for item in items:
        by_chapter.setdefault(item.chapter_key, []).append(item)
    for chapter_key in _ordered_chapter_keys(items):
        chapter_items = by_chapter[chapter_key]
        token_sets = [content_tokens(item.text) for item in chapter_items]
        assigned = [False] * len(chapter_items)
        for index, item in enumerate(chapter_items):
            if assigned[index]:
                continue
            group = [index]
            assigned[index] = True
            for other in range(index + 1, len(chapter_items)):
                if assigned[other]:
                    continue
                best = max(similarity(token_sets[g], token_sets[other]) for g in group)
                if best >= SIMILARITY_THRESHOLD:
                    group.append(other)
                    assigned[other] = True
            members = [chapter_items[g] for g in group]
            cluster = Cluster(chapter_key=chapter_key, element=members[0].element, kind=members[0].kind, items=members)
            clusters.append(cluster)
    clusters.sort(key=lambda c: (c.chapter_key, -c.reader_count, c.element))
    return clusters
