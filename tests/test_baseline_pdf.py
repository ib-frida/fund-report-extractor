"""End-to-end check of the baseline on a synthetic report.

tests/fixtures/synthetic_report.pdf is made-up data: three funds and a total
row whose figures reconcile, except Gamma Growth III, whose TVPI is printed as
1.90x when the identity gives 0.90x. The validators must catch exactly that.
"""

from pathlib import Path

import pytest

from fundx.baseline import extract_pdf
from fundx.validate import validate_rows

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_report.pdf"


@pytest.fixture(scope="module")
def rows():
    return extract_pdf(FIXTURE, report_id="synthetic")


def test_baseline_reads_all_rows(rows):
    names = [r.fund_name for r in rows]
    assert names == ["Alpha Fund I, L.P.", "Beta Partners II", "Gamma Growth III", "Total"]
    assert rows[-1].is_total_row


def test_baseline_parses_values(rows):
    alpha = rows[0]
    assert alpha.vintage_year == 2016
    assert alpha.commitment == 10_000_000
    assert alpha.net_irr == pytest.approx(0.142)
    assert (alpha.tvpi, alpha.dpi) == (1.8, 1.3)
    assert rows[2].net_irr == pytest.approx(-0.041)


def test_validators_flag_only_the_planted_error(rows):
    flags = validate_rows(rows)
    assert [(f.fund_name, f.reason, f.expected) for f in flags] == [("Gamma Growth III", "TVPI_IDENTITY", 0.9)]
