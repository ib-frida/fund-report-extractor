# fund-report-extractor

> **Status: work in progress (weekend 1 of 3).** Results go here once the gold set is labelled.
>
> *Pitch to fill in:* I used an LLM to extract private-equity fund performance tables from public pension-fund reports, then checked every number with automated validators. The validators caught **X%** of extraction errors, and field accuracy was **Y%** against a hand-labelled gold set (baseline parser: **Z%**).

## What it does

1. **Download** the source PDFs listed in `config/sources.yaml`, recording a SHA-256 for each.
2. **Extract** fund rows two ways:
   - a baseline (`pdfplumber` tables + header matching, no AI)
   - an LLM extractor with a strict JSON schema (weekend 2)
3. **Validate** every number. Each failure gets a reason code:
   - `TVPI_IDENTITY`: TVPI should equal (distributions + NAV) / contributions
   - `DPI_IDENTITY`: DPI should equal distributions / contributions
   - `TOTAL_MISMATCH`: the report's total row should equal the sum of its fund rows
   - `EXTRACTOR_DISAGREE`: the LLM and the baseline read different values
   - range checks: negative amounts, an IRR left as a percent, DPI above TVPI
4. **Evaluate** against a hand-labelled gold set: field-level accuracy, with missing rows counted as wrong.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows; use source .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
pytest -q
```

Then:

```bash
fundx download                                   # after adding URLs to config/sources.yaml
fundx baseline                                   # writes data/interim/<id>_baseline.csv
fundx validate data/interim/<id>_baseline.csv    # writes outputs/exceptions.csv
fundx evaluate data/interim/<id>_baseline.csv --gold data/gold/gold.csv
```

With Docker: `docker build -t fundx .` and then `docker run fundx`. The container runs the tests.

## Project layout

```
config/sources.yaml   reports to process (ids, URLs, units, pages)
data/raw/             downloaded PDFs + manifest (git-ignored)
data/gold/            hand-labelled rows (gold_template.csv shows the format)
data/interim/         extractor outputs (git-ignored)
src/fundx/            schema, parsing, baseline, validators, evaluation, CLI
tests/                unit tests (no network, no API key)
docs/plan.md          project plan
```

## Data and licensing

Source reports are public documents from their publishers. This repo doesn't redistribute them: `fundx download` fetches them from the original URLs. Check each publisher's terms before committing any extracted data.

## Status

- [x] Schema, number parsing, validators, evaluation, CLI, tests, CI, Docker
- [ ] Weekend 1: choose 3-5 reports, run the baseline, label the gold set (`data/gold/gold.csv`), record baseline accuracy
- [ ] Weekend 2: LLM extractor with cached responses; agreement checks; exception report
- [ ] Weekend 3: results, chart, write-up of what the validators missed

Personal portfolio project by Frida Ibarra.
