"""Baseline extractor: pdfplumber tables + header keyword mapping, no AI.

This is the comparison point for the LLM extractor. It is deliberately simple:
it maps each table column to a schema field by its header text, then parses
cells with the rules in parsing.py. Publishers with unusual headers can pin
the mapping in config/sources.yaml (`columns:`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pdfplumber

from .parsing import parse_number, parse_percent, parse_year
from .schema import FundRow

# Header keywords -> schema field. First match wins, so order matters
# (e.g. "net irr" must be tested before generic "irr").
HEADER_KEYWORDS: list[tuple[str, str]] = [
    ("vintage", "vintage_year"),
    ("fund name", "fund_name"),
    ("partnership", "fund_name"),
    ("investment name", "fund_name"),
    ("fund", "fund_name"),
    ("commitment", "commitment"),
    ("committed", "commitment"),
    ("contribut", "contributed"),
    ("paid-in", "contributed"),
    ("paid in", "contributed"),
    ("distribut", "distributed"),
    ("nav", "nav"),
    ("net asset", "nav"),
    ("market value", "nav"),
    ("remaining value", "nav"),
    ("net irr", "net_irr"),
    ("irr", "net_irr"),
    ("tvpi", "tvpi"),
    ("investment multiple", "tvpi"),
    ("total value", "tvpi"),
    ("dpi", "dpi"),
]

TOTAL_MARKERS = ("total", "subtotal", "sub-total", "grand total")


def map_header(header: list[Optional[str]], override: Optional[dict] = None) -> dict[int, str]:
    """Return {column index: schema field} for a table header row."""
    mapping: dict[int, str] = {}
    used: set[str] = set()
    if override:
        for idx, field in override.items():
            mapping[int(idx)] = field
        return mapping
    for i, cell in enumerate(header):
        text = (cell or "").replace("\n", " ").strip().lower()
        for key, field in HEADER_KEYWORDS:
            if key in text and field not in used:
                mapping[i] = field
                used.add(field)
                break
    return mapping


def row_from_cells(cells: list[Optional[str]], mapping: dict[int, str], report_id: str, page: int, unit: str) -> Optional[FundRow]:
    values: dict = {}
    for i, field in mapping.items():
        cell = cells[i] if i < len(cells) else None
        if field == "fund_name":
            name = (cell or "").replace("\n", " ").strip()
            if name:
                values["fund_name"] = name
        elif field == "vintage_year":
            values[field] = parse_year(cell)
        elif field == "net_irr":
            values[field] = parse_percent(cell)
        else:
            values[field] = parse_number(cell)
    name = values.get("fund_name")
    if not name:
        return None
    numeric = [v for k, v in values.items() if k != "fund_name" and v is not None]
    if not numeric:
        return None  # section headings and footnotes have a name but no numbers
    is_total = name.lower().startswith(TOTAL_MARKERS)
    return FundRow(report_id=report_id, page=page, unit=unit, is_total_row=is_total, source="baseline", **values)


def extract_pdf(pdf_path: str | Path, report_id: str, unit: str = "USD", pages: Optional[list[int]] = None, columns: Optional[dict] = None) -> list[FundRow]:
    """Extract fund rows from every table in the PDF (or the given 1-based pages)."""
    rows: list[FundRow] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            if pages and pno not in pages:
                continue
            for table in page.extract_tables():
                if not table or len(table) < 2:
                    continue
                mapping = map_header(table[0], columns)
                if "fund_name" not in mapping.values() or len(mapping) < 3:
                    continue  # not a fund performance table
                for cells in table[1:]:
                    row = row_from_cells(cells, mapping, report_id, pno, unit)
                    if row is not None:
                        rows.append(row)
    return rows
