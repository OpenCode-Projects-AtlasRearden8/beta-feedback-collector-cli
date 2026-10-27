"""Split feedback into nitpicks (line/prose-level) vs plot-level flags.

If the sheet tags comments explicitly (type/severity columns or inline
[nitpick]/[plot] prefixes), trust the tag. Otherwise fall back to keyword
heuristics over the comment text.
"""

from __future__ import annotations

import re

from .models import NITPICK, PLOT


NITPICK_WORDS = (
    "typo", "spelling", "misspell", "grammar", "grammatical", "comma",
    "semicolon", "punctuation", "capitalization", "spacing", "italics",
    "italic", "formatting", "word choice", "wording", "wording of",
    "repeated word", "repeated phrase", "hyphen", "tense", "paragraph break",
    "line break", "dangling modifier", "passive voice",
)

PLOT_WORDS = (
    "plot", "pacing", "storyline", "plotline", "ending", "twist", "climax",
    "stakes", "motivation", "character arc", "arc", "continuity",
    "timeline", "worldbuilding", "world-building", "setting", "reveal",
    "relationship", "romance", "backstory", "foreshadow", "payoff",
    "confused", "confusing", "didn't buy", "did not buy", "unearned",
    "too slow", "too fast", "dragged", "rushed", "magic system", "rule",
)

NITPICK_RE = re.compile(
    r"\b(" + "|".join(w.replace(" ", r"\s+") for w in NITPICK_WORDS) + r")\b",
    re.IGNORECASE,
)
PLOT_RE = re.compile(
    r"\b(" + "|".join(w.replace(" ", r"\s+") for w in PLOT_WORDS) + r")\b",
    re.IGNORECASE,
)
TAG_RE = re.compile(r"^\s*[\[\(]?\s*(nitpick|nit|plot|major|minor|story|structure)\b[\]\):]?", re.IGNORECASE)


def _from_tag(text: str):
    match = TAG_RE.match(text)
    if not match:
        return None
    word = match.group(1).lower()
    if word in ("nitpick", "nit", "minor"):
        return NITPICK
    if word in ("plot", "major", "story", "structure"):
        return PLOT
    return None


def classify(text: str, hinted_kind=None) -> str:
    """Return NITPICK or PLOT for a comment."""
    for candidate in (hinted_kind, _from_tag(text)):
        if candidate == NITPICK or candidate == PLOT:
            return candidate
    text_l = text.lower()
    nitpick_hits = len(NITPICK_RE.findall(text_l))
    plot_hits = len(PLOT_RE.findall(text_l))
    if nitpick_hits and plot_hits:
        return PLOT if plot_hits >= nitpick_hits else NITPICK
    if nitpick_hits:
        return NITPICK
    if plot_hits:
        return PLOT
    return NITPICK
