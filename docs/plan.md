# Portfolio project plan: Verified extraction of private-fund performance data

*Drafted 2026-11-10. Target: about 3 weekends. Repo name suggestion: `fund-report-extractor`.*

## The pitch (top of the README)

> I used an LLM to extract private-equity fund performance tables from public pension-fund reports, then checked every number with automated validators. The validators caught X% of extraction errors, and field accuracy was Y% against a hand-labelled gold set (baseline parser: Z%).

Fill X, Y and Z with real results. They are the point of the project.

## Why this project

- **MSCI PCS Data Ops role:** hands-on AI-assisted extraction and validation; challenging outputs; auditability.
- **MSCI Implementation role:** validate fund market values, contributions and returns, then triage and document differences.
- **MSCI Quant role:** applied statistics on financial data; it shows interest in the domain.
- **H-E-B AI Specialist role:** LLM APIs, Document AI, Docker, CI/CD.
- It extends your strongest story: the 33-value verification pass in your dissertation.

## Data

**Primary source:** public pension funds publish private-equity fund performance tables as PDFs. CalPERS and CalSTRS are examples. They are public records.
- Typical columns: fund name, vintage year, commitment, contributions, distributions, NAV, net IRR, TVPI/DPI.
- This is the same kind of data MSCI's Private Capital Solutions team handles.
- Pick 3-5 reports from 2-3 publishers so the layouts differ.
- Check each publisher's terms before committing the PDFs to the repo. If unsure, commit a download script instead of the files.

**Stretch:** Mexican private-capital vehicles (CKDs/CERPIs) report on BMV. Adding one gives the project a Mexico angle.

## Pipeline

1. **Ingest.** Download the PDFs and extract page text and tables with `pdfplumber`.
2. **Baseline.** Use pure `pdfplumber` table extraction plus cleaning rules. This is your comparison point.
3. **LLM extraction.** Send each page to the Claude API with a strict JSON schema (`pydantic` model). Use one record per fund row. Cache every response to disk so runs are reproducible and cheap.
4. **Validators.** Each failure gets a reason code:
   - Schema and type: numbers parse; IRR and multiples are in plausible ranges.
   - Arithmetic identities: TVPI ≈ (distributions + NAV) / contributions, and DPI ≈ distributions / contributions, within rounding tolerance.
   - Totals: the sum of the rows matches the report's total row.
   - Cross-check: LLM value vs baseline parser value. Flag any field where they disagree.
   - Cross-period (if you have two reports from the same fund): cumulative contributions don't decrease.
5. **Exception report.** Write a CSV of flagged fields with reason code, LLM value, baseline value and page number. This is your "triage and document differences" evidence.
6. **Evaluation.**
   - Hand-label a gold set of about 150-200 rows from 2-3 reports. You built a gold standard in your Information Retrieval module, so mention it.
   - Report field-level accuracy for the LLM and the baseline.
   - Report the share of LLM errors the validators caught, and the false-alarm rate.

## Engineering (cheap, but visible)

- `pytest` tests on 2-3 fixture pages, using cached LLM responses so tests need no API key.
- A GitHub Actions workflow that runs the tests on every push.
- A `Dockerfile` that runs the pipeline end to end on the fixtures.
- A `.env.example` for the API key. Never commit the key.
- Optional: a small Streamlit page that shows the exception queue.

## Timeline

| Weekend | Work | Done when |
|---|---|---|
| 1 | Pick reports, download script, baseline parser, label the gold set | Gold CSV exists; baseline accuracy number computed |
| 2 | LLM extraction with schema and caching, validators, exception CSV | Every row has values plus pass/flag status |
| 3 | Evaluation, README with results and one chart, tests, CI, Dockerfile | Repo pinned; README leads with the real numbers |

## README structure

1. One-paragraph pitch with the three numbers.
2. One chart: accuracy by field (LLM vs baseline), or errors caught by validator type.
3. How the validation works (the identities, in plain words).
4. What went wrong and what the validators missed. Be honest; this is what reviewers trust.
5. How to run (Docker, or `pip install` + one command).
6. Data sources and licence notes.

## How to use it in applications

- **CV:** one line under Projects, for example "Built an LLM extraction pipeline for private-fund performance data with automated validation; caught X% of errors; Y% field accuracy vs Z% baseline."
- **MSCI interviews:** use it to tell the "challenging an AI output" story.
- **Wording:** describe it as a personal portfolio project, not production work.

## Before you start

- Confirm you are comfortable with API costs. Caching keeps re-runs free.
- Learn the basic terms (commitment, contributions, distributions, NAV, IRR, TVPI, DPI). You need them for MSCI interviews anyway.
