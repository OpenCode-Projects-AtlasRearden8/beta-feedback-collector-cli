"""Detect contradictory feedback between readers on the same chapter."""

from __future__ import annotations

from .textutils import tokens

POSITIVE_WORDS = frozenset(
    """loved liked enjoyed great gripping vivid compelling strong charming
    delightful funny awesome excellent best favorite works shines warm
    satisfying satisfying""".split()
)
NEGATIVE_WORDS = frozenset(
    """hated disliked boring weak slow confusing dragged flat dull unconvincing
    annoying cringe eye-roll stiff rushed jarring disconnect misplaced""".split()
)
ANTONYM_PAIRS = [
    ("slow", "fast"),
    ("slow", "rushed"),
    ("dragged", "rushed"),
    ("slowed", "rushed"),
    ("too-short", "too-long"),
    ("need-more", "need-less"),
    ("more", "less"),
    ("clear", "confusing"),
    ("earned", "unearned"),
    ("believable", "unconvincing"),
]


def sentiment(text: str):
    toks = set(tokens(text))
    hit_pos = bool(toks & POSITIVE_WORDS)
    hit_neg = bool(toks & NEGATIVE_WORDS)
    if hit_pos and not hit_neg:
        return 1
    if hit_neg and not hit_pos:
        return -1
    return 0


def _antonym_conflict(text_a: str, text_b: str) -> bool:
    toks_a = set(tokens(text_a))
    toks_b = set(tokens(text_b))
    for left, right in ANTONYM_PAIRS:
        if (left in toks_a and right in toks_b) or (left in toks_b and right in toks_a):
            return True
    return False


def _shared_content(text_a: str, text_b: str) -> bool:
    toks_a = set(tokens(text_a))
    toks_b = set(tokens(text_b))
    return bool(toks_a & toks_b)


def find_contradictions(items) -> list:
    """Return (reader_a, text_a, reader_b, text_b, chapter_key) tuples that clash."""
    contradictions = []
    by_chapter = {}
    for item in items:
        by_chapter.setdefault(item.chapter_key, []).append(item)
    seen_texts = set()
    for chapter_key, chapter_items in sorted(by_chapter.items()):
        for a in range(len(chapter_items)):
            for b in range(a + 1, len(chapter_items)):
                first, second = chapter_items[a], chapter_items[b]
                if first.reader == second.reader:
                    continue
                same_topic = _shared_content(first.text, second.text)
                clash = (
                    (sentiment(first.text) == 1 and sentiment(second.text) == -1)
                    or (sentiment(first.text) == -1 and sentiment(second.text) == 1)
                    or _antonym_conflict(first.text, second.text)
                )
                if not (same_topic and clash):
                    continue
                left = (first.reader, first.text)
                right = (second.reader, second.text)
                pair_key = tuple(sorted([left[1], right[1]]))
                if pair_key in seen_texts:
                    continue
                seen_texts.add(pair_key)
                contradictions.append((*left, *right, chapter_key))
    return contradictions
