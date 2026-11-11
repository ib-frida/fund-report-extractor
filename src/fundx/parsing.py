"""Turn the strings printed in financial tables into numbers.

Handles the common report conventions: thousands separators, currency symbols,
parentheses for negatives, percentages, 'x' multiples and dash/n.m. placeholders.
"""

from __future__ import annotations

import re
from typing import Optional

_EMPTY = {"", "-", "--", "—", "–", "n/a", "na", "n.a.", "nm", "n.m.", "n.m", "*"}


def parse_number(text: object) -> Optional[float]:
    """Parse a table cell into a float, or None if it holds no number.

    >>> parse_number("$1,234.5")
    1234.5
    >>> parse_number("(12.0)")
    -12.0
    >>> parse_number("1.45x")
    1.45
    """
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)
    s = str(text).strip().lower()
    if s in _EMPTY:
        return None
    s = re.sub(r"[$€£¥,\s]|usd|mxn", "", s)
    s = s.rstrip("%x×")
    # Sign: a leading minus and accounting parentheses each flip it, so
    # "(3.5)" and "-3.5" are negative while "-(3.5)" is positive.
    negative = False
    if s.startswith("-"):
        negative, s = not negative, s[1:]
    if s.startswith("(") and s.endswith(")"):
        negative, s = not negative, s[1:-1]
    if s.startswith("-"):
        negative, s = not negative, s[1:]
    s = s.rstrip("%x×")  # "(4.1%)" keeps its % inside the parentheses
    if s in _EMPTY:
        return None
    try:
        value = float(s)
    except ValueError:
        return None
    return -value if negative else value


def parse_percent(text: object) -> Optional[float]:
    """Parse a percentage cell into a fraction: '12.5%' -> 0.125, '(3.1)%' -> -0.031."""
    value = parse_number(text)
    return None if value is None else value / 100.0


def parse_year(text: object) -> Optional[int]:
    """Parse a vintage year; returns None unless it is a plausible 4-digit year."""
    value = parse_number(text)
    if value is None or not value.is_integer():
        return None
    year = int(value)
    return year if 1970 <= year <= 2100 else None


def normalise_name(name: str) -> str:
    """Normalise a fund name for matching rows across extractors."""
    s = name.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\b(l ?p|llc|ltd|inc|the|fund)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()
