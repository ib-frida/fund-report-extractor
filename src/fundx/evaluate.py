"""Score an extractor's rows against the hand-labelled gold set.

Rows are matched on (report_id, normalised fund name). A field is correct when
it is within the same tolerance the validators use. Missing rows count as wrong
for every field, so a cautious extractor cannot game accuracy by skipping rows.
"""

from __future__ import annotations

import pandas as pd

from .parsing import normalise_name
from .schema import NUMERIC_FIELDS, FundRow
from .validate import ABS_TOL, REL_TOL


def _key(r: FundRow) -> tuple[str, str]:
    return (r.report_id, normalise_name(r.fund_name))


def _equal(a, b) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= max(ABS_TOL, REL_TOL * abs(float(b)))


def evaluate(pred: list[FundRow], gold: list[FundRow]) -> dict:
    gold_rows = {_key(r): r for r in gold if not r.is_total_row}
    pred_rows = {_key(r): r for r in pred if not r.is_total_row}
    matched = gold_rows.keys() & pred_rows.keys()
    missing = sorted(gold_rows.keys() - pred_rows.keys())
    extra = sorted(pred_rows.keys() - gold_rows.keys())

    per_field = []
    for field in NUMERIC_FIELDS:
        labelled = [k for k, g in gold_rows.items() if getattr(g, field) is not None]
        if not labelled:
            continue
        correct = sum(1 for k in labelled if k in matched and _equal(getattr(pred_rows[k], field), getattr(gold_rows[k], field)))
        per_field.append({"field": field, "labelled": len(labelled), "correct": correct, "accuracy": correct / len(labelled)})

    fields_df = pd.DataFrame(per_field, columns=["field", "labelled", "correct", "accuracy"])
    total_labelled = int(fields_df["labelled"].sum()) if not fields_df.empty else 0
    total_correct = int(fields_df["correct"].sum()) if not fields_df.empty else 0
    return {
        "gold_rows": len(gold_rows),
        "matched_rows": len(matched),
        "missing_rows": missing,
        "extra_rows": extra,
        "per_field": fields_df,
        "overall_accuracy": (total_correct / total_labelled) if total_labelled else None,
    }


def format_report(result: dict, label: str) -> str:
    lines = [f"## {label}", ""]
    lines.append(f"Gold rows: {result['gold_rows']} | matched: {result['matched_rows']} | missing: {len(result['missing_rows'])} | extra: {len(result['extra_rows'])}")
    acc = result["overall_accuracy"]
    lines.append(f"Overall field accuracy: {acc:.1%}" if acc is not None else "Overall field accuracy: n/a (no labelled fields)")
    lines.append("")
    if not result["per_field"].empty:
        df = result["per_field"].copy()
        df["accuracy"] = df["accuracy"].map(lambda v: f"{v:.1%}")
        lines.append(df.to_markdown(index=False))
    return "\n".join(lines)
