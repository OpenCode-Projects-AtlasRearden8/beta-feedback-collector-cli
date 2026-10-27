"""Lightweight text utilities: tokenization and stopword filtering.

Kept tiny and dependency-free on purpose; the clustering is intentionally
heuristic (beta feedback is short, conversational prose).
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9']+")

STOPWORDS = frozenset(
    """a about after all also am an and any as at be because been before being
    but by can could did do does doing don for from get gets got had has have
    having he her here hers him his how i if in into is it its just like me
    more most my no not of off on once only or other our out over own re s
    she should so some t than that the their them then there these they this
    those to too up us ve was we were what when where which while who whom
    why will with would you your yours""".split(),
)
# keep comparison pairs out of stopwords so antonym detection works
_STOPWORD_REMOVALS = frozenset({"more", "less", "slow", "fast"})
STOPWORDS = frozenset(w for w in STOPWORDS if w not in _STOPWORD_REMOVALS)

# Words where naive plural-stripping would mangle meaning.
_KEEP_AS_IS = frozenset({"was", "has", "does", "its", "this"})


def tokens(text: str) -> list:
    cleaned = text.lower().replace("'", "")
    toks = _TOKEN_RE.findall(cleaned)
    out = []
    for tok in toks:
        if tok in STOPWORDS:
            continue
        if tok.endswith("s") and not tok.endswith("ss") and tok not in _KEEP_AS_IS and len(tok) > 3:
            tok = tok[:-1]
        out.append(tok)
    return out


def content_tokens(text: str) -> set:
    return set(tokens(text))
