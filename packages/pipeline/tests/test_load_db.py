"""Tests for database-loading value normalization."""

from __future__ import annotations

import pytest

from scripts.load_db import _str_or_none


@pytest.mark.parametrize("value", [float("nan"), "NaN", None])
def test_str_or_none_returns_none_for_missing_values(value):
    assert _str_or_none(value) is None


def test_str_or_none_strips_real_text():
    assert _str_or_none("  Dallas, TX ") == "Dallas, TX"
