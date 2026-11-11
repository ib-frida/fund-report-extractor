"""Read and write FundRow tables as CSV."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import FundRow

COLUMNS = list(FundRow.model_fields)


def rows_to_csv(rows: list[FundRow], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([r.model_dump() for r in rows], columns=COLUMNS)
    df.to_csv(path, index=False)


def rows_from_csv(path: str | Path, source: str | None = None) -> list[FundRow]:
    df = pd.read_csv(path)
    df = df.astype(object).where(pd.notna(df), None)
    rows = []
    for rec in df.to_dict(orient="records"):
        rec = {k: v for k, v in rec.items() if k in COLUMNS}
        if isinstance(rec.get("is_total_row"), str):
            rec["is_total_row"] = rec["is_total_row"].strip().lower() in {"true", "1", "yes"}
        if rec.get("is_total_row") is None:
            rec["is_total_row"] = False
        if source:
            rec["source"] = source
        rows.append(FundRow(**{k: v for k, v in rec.items() if v is not None}))
    return rows
