"""Tests for nitpick vs plot-level classification."""

import pytest

from betafeedback.classify import classify
from betafeedback.models import NITPICK, PLOT


def test_explicit_nitpick_tag():
    assert classify("(nitpick) Comma issue", None) == NITPICK
    assert classify("[minor] word choice", None) == NITPICK
    assert classify("nit: repeated word", None) == NITPICK
    assert classify("plot: motive unclear", None) == PLOT
    assert classify("[major] no stakes yet", None) == PLOT


def test_hinted_kind_wins_when_no_inline_tag():
    assert classify("nothing structural here", "plot") == PLOT
    assert classify("nothing structural here", "nitpick") == NITPICK


def test_keyword_heuristics():
    assert classify("repeated word in the section", None) == NITPICK
    assert classify("typo: should be 'there'", None) == NITPICK
    assert classify("the reveal comes unearned, pacing rushed too fast", None) == PLOT
    assert classify("worldbuilding is jarring here", None) == PLOT
    assert classify("a small formatting nit with spacing", None) == NITPICK


def test_default_is_plot_level():
    assert classify("this chapter felt flat and unearned", None) == PLOT


def test_classify_never_lowcases_plain_word():
    # a plain sentence with no markers stays nitpick-level
    assert classify("text is fine here", "nitpick") == NITPICK
