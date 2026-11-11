import pytest

from fundx.baseline import map_header, row_from_cells
from fundx.evaluate import evaluate, format_report
from fundx.io import rows_from_csv, rows_to_csv
from fundx.schema import FundRow


def gold_rows():
    return [
        FundRow(report_id="r1", page=1, fund_name="Alpha Fund I, L.P.", contributed=100.0, nav=80.0, tvpi=1.2, source="gold"),
        FundRow(report_id="r1", page=1, fund_name="Beta Partners II", contributed=50.0, nav=60.0, tvpi=1.5, source="gold"),
    ]


def test_evaluate_counts_missing_rows_as_wrong():
    pred = [FundRow(report_id="r1", page=1, fund_name="alpha fund I LP", contributed=100.0, nav=80.0, tvpi=1.2)]
    result = evaluate(pred, gold_rows())
    assert result["matched_rows"] == 1
    assert len(result["missing_rows"]) == 1
    assert result["overall_accuracy"] == pytest.approx(0.5)
    assert "Overall field accuracy: 50.0%" in format_report(result, "test")


def test_csv_round_trip(tmp_path):
    path = tmp_path / "rows.csv"
    rows_to_csv(gold_rows(), path)
    back = rows_from_csv(path)
    assert [r.model_dump() for r in back] == [r.model_dump() for r in gold_rows()]


def test_gold_template_loads():
    rows = rows_from_csv("data/gold/gold_template.csv", source="gold")
    assert rows[0].net_irr == pytest.approx(0.142)
    assert rows[0].is_total_row is False


def test_baseline_header_mapping_and_row_parsing():
    header = ["Fund Name", "Vintage\nYear", "Commitment ($)", "Paid-In Capital", "Distributions", "Market Value", "Net IRR", "TVPI"]
    mapping = map_header(header)
    assert mapping == {0: "fund_name", 1: "vintage_year", 2: "commitment", 3: "contributed", 4: "distributed", 5: "nav", 6: "net_irr", 7: "tvpi"}

    cells = ["Alpha Fund I", "2018", "$10,000", "9,000", "4,500", "6,300", "11.2%", "1.20x"]
    r = row_from_cells(cells, mapping, "r1", 3, "USD")
    assert (r.vintage_year, r.contributed, r.net_irr, r.tvpi) == (2018, 9000.0, pytest.approx(0.112), 1.2)

    assert row_from_cells(["Buyout", None, None, None, None, None, None, None], mapping, "r1", 3, "USD") is None
    total = row_from_cells(["Total", "", "$10,000", "9,000", "4,500", "6,300", "", ""], mapping, "r1", 3, "USD")
    assert total.is_total_row
