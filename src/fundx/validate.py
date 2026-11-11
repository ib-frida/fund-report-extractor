"""Validators: every extracted number must survive these checks or be flagged.

Each check returns a list of Flag objects with a reason code, so the exception
report can say *why* a value is suspect, not just that it is.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Optional

from .schema import FundRow

# Relative tolerance for identities. Reports round multiples to 2 dp, so allow
# 0.01 absolute or 1% relative, whichever is larger.
ABS_TOL = 0.01
REL_TOL = 0.01


@dataclass
class Flag:
    report_id: str
    page: int
    fund_name: str
    field: str
    reason: str
    actual: Optional[float]
    expected: Optional[float] = None
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(ABS_TOL, REL_TOL * abs(b))


def _flag(row: FundRow, field: str, reason: str, actual, expected=None, detail="") -> Flag:
    return Flag(row.report_id, row.page, row.fund_name, field, reason, actual, expected, detail)


def check_ranges(row: FundRow) -> list[Flag]:
    """Values outside plausible ranges usually mean a misread column or scale."""
    flags = []
    for field in ("commitment", "contributed", "distributed", "nav"):
        v = getattr(row, field)
        if v is not None and v < 0:
            flags.append(_flag(row, field, "NEGATIVE_AMOUNT", v))
    if row.net_irr is not None and not -1.0 <= row.net_irr <= 3.0:
        flags.append(_flag(row, "net_irr", "IRR_OUT_OF_RANGE", row.net_irr, detail="expected a fraction between -100% and 300%"))
    for field in ("tvpi", "dpi"):
        v = getattr(row, field)
        if v is not None and not 0.0 <= v <= 20.0:
            flags.append(_flag(row, field, "MULTIPLE_OUT_OF_RANGE", v))
    if row.dpi is not None and row.tvpi is not None and row.dpi > row.tvpi + ABS_TOL:
        flags.append(_flag(row, "dpi", "DPI_ABOVE_TVPI", row.dpi, row.tvpi))
    return flags


def check_identities(row: FundRow) -> list[Flag]:
    """TVPI = (distributed + NAV) / contributed; DPI = distributed / contributed."""
    flags = []
    c, d, n = row.contributed, row.distributed, row.nav
    if c in (None, 0) or d is None:
        return flags
    if row.dpi is not None:
        expected = d / c
        if not _close(row.dpi, expected):
            flags.append(_flag(row, "dpi", "DPI_IDENTITY", row.dpi, round(expected, 4)))
    if row.tvpi is not None and n is not None:
        expected = (d + n) / c
        if not _close(row.tvpi, expected):
            flags.append(_flag(row, "tvpi", "TVPI_IDENTITY", row.tvpi, round(expected, 4)))
    return flags


def check_totals(rows: Iterable[FundRow]) -> list[Flag]:
    """The report's total row must equal the sum of its fund rows, per report."""
    flags = []
    by_report: dict[str, list[FundRow]] = {}
    for r in rows:
        by_report.setdefault(r.report_id, []).append(r)
    for report_rows in by_report.values():
        totals = [r for r in report_rows if r.is_total_row]
        funds = [r for r in report_rows if not r.is_total_row]
        if len(totals) != 1 or not funds:
            continue  # subtotals need grouping rules per publisher; add when needed
        total = totals[0]
        for field in ("commitment", "contributed", "distributed", "nav"):
            reported = getattr(total, field)
            values = [getattr(r, field) for r in funds]
            if reported is None or any(v is None for v in values):
                continue
            summed = sum(values)
            if not _close(reported, summed):
                flags.append(_flag(total, field, "TOTAL_MISMATCH", reported, round(summed, 2)))
    return flags


def check_agreement(primary: FundRow, other: FundRow, fields: Iterable[str]) -> list[Flag]:
    """Flag fields where two extractors (e.g. LLM vs baseline) disagree."""
    flags = []
    for field in fields:
        a, b = getattr(primary, field), getattr(other, field)
        if a is None or b is None:
            continue
        if not _close(float(a), float(b)):
            flags.append(_flag(primary, field, "EXTRACTOR_DISAGREE", a, b, detail=f"other source: {other.source}"))
    return flags


def validate_rows(rows: list[FundRow]) -> list[Flag]:
    """Run all single-source checks over a list of rows."""
    flags: list[Flag] = []
    for r in rows:
        if r.is_total_row:
            continue
        flags += check_ranges(r)
        flags += check_identities(r)
    flags += check_totals(rows)
    return flags
