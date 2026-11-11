"""Record schema for one fund row in a performance report.

Monetary fields are stored in the report's own unit (see `unit`), never rescaled,
so every value can be traced back to the page it came from.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Fields compared during evaluation, in display order.
NUMERIC_FIELDS = [
    "vintage_year",
    "commitment",
    "contributed",
    "distributed",
    "nav",
    "net_irr",
    "tvpi",
    "dpi",
]


class FundRow(BaseModel):
    """One row of a private-equity fund performance table."""

    report_id: str = Field(description="Short id of the source report, e.g. 'calpers-2025q4'")
    page: int = Field(ge=1, description="1-based PDF page the row was read from")
    fund_name: str
    vintage_year: Optional[int] = None
    commitment: Optional[float] = None
    contributed: Optional[float] = None
    distributed: Optional[float] = None
    nav: Optional[float] = Field(default=None, description="Net asset value / remaining value")
    net_irr: Optional[float] = Field(default=None, description="Net IRR as a fraction: 12.5% -> 0.125")
    tvpi: Optional[float] = Field(default=None, description="Total value to paid-in multiple")
    dpi: Optional[float] = Field(default=None, description="Distributions to paid-in multiple")
    unit: str = Field(default="USD", description="Currency and scale as printed, e.g. 'USD' or 'USD millions'")
    is_total_row: bool = Field(default=False, description="True for a report's total/subtotal line")
    source: str = Field(default="unknown", description="Extractor that produced the row: 'baseline', 'llm' or 'gold'")
