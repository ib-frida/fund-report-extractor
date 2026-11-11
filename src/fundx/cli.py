"""Command line: fundx download | baseline | validate | evaluate."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from . import baseline, download, io
from .evaluate import evaluate, format_report
from .validate import validate_rows


def _sources(config: str) -> list[dict]:
    with open(config, encoding="utf-8") as fh:
        return (yaml.safe_load(fh) or {}).get("reports", [])


def cmd_download(args) -> None:
    download.download_all(args.config, args.raw_dir, force=args.force)


def cmd_baseline(args) -> None:
    for src in _sources(args.config):
        pdf = Path(args.raw_dir) / f"{src['id']}.pdf"
        if not pdf.exists():
            print(f"skip  {src['id']}: {pdf} not found (run `fundx download`)")
            continue
        rows = baseline.extract_pdf(pdf, src["id"], unit=src.get("unit", "USD"), pages=src.get("pages"), columns=src.get("columns"))
        out = Path(args.out_dir) / f"{src['id']}_baseline.csv"
        io.rows_to_csv(rows, out)
        print(f"{src['id']}: {len(rows)} rows -> {out}")


def cmd_validate(args) -> None:
    rows = io.rows_from_csv(args.rows)
    flags = validate_rows(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([f.to_dict() for f in flags]).to_csv(out, index=False)
    print(f"{len(rows)} rows checked, {len(flags)} flags -> {out}")
    if flags:
        print(pd.Series([f.reason for f in flags]).value_counts().to_string())


def cmd_evaluate(args) -> None:
    pred = io.rows_from_csv(args.pred)
    gold = io.rows_from_csv(args.gold, source="gold")
    report = format_report(evaluate(pred, gold), label=args.label or Path(args.pred).stem)
    print(report)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report + "\n", encoding="utf-8")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="fundx", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("download", help="download reports listed in the config")
    d.add_argument("--config", default="config/sources.yaml")
    d.add_argument("--raw-dir", default="data/raw")
    d.add_argument("--force", action="store_true")
    d.set_defaults(func=cmd_download)

    b = sub.add_parser("baseline", help="run the pdfplumber baseline extractor")
    b.add_argument("--config", default="config/sources.yaml")
    b.add_argument("--raw-dir", default="data/raw")
    b.add_argument("--out-dir", default="data/interim")
    b.set_defaults(func=cmd_baseline)

    v = sub.add_parser("validate", help="run validators on an extracted CSV")
    v.add_argument("rows")
    v.add_argument("--out", default="outputs/exceptions.csv")
    v.set_defaults(func=cmd_validate)

    e = sub.add_parser("evaluate", help="score extracted rows against the gold set")
    e.add_argument("pred")
    e.add_argument("--gold", default="data/gold/gold.csv")
    e.add_argument("--label")
    e.add_argument("--out")
    e.set_defaults(func=cmd_evaluate)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
