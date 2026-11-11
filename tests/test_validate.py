from fundx.schema import FundRow
from fundx.validate import check_agreement, check_identities, check_ranges, check_totals, validate_rows


def row(**kw):
    base = dict(report_id="r1", page=1, fund_name="Fund A", contributed=100.0, distributed=40.0, nav=80.0, tvpi=1.2, dpi=0.4)
    base.update(kw)
    return FundRow(**base)


def reasons(flags):
    return sorted(f.reason for f in flags)


def test_consistent_row_passes():
    assert check_identities(row()) == []
    assert check_ranges(row(net_irr=0.12)) == []


def test_tvpi_identity_catches_misread_multiple():
    flags = check_identities(row(tvpi=2.1))
    assert reasons(flags) == ["TVPI_IDENTITY"]
    assert flags[0].expected == 1.2


def test_dpi_identity_tolerates_rounding():
    assert check_identities(row(distributed=40.4, dpi=0.40)) == []  # 0.404 rounds to 0.40


def test_ranges_catch_percent_left_unscaled():
    flags = check_ranges(row(net_irr=12.5))  # 12.5 instead of 0.125
    assert reasons(flags) == ["IRR_OUT_OF_RANGE"]


def test_dpi_above_tvpi_is_flagged():
    assert "DPI_ABOVE_TVPI" in reasons(check_ranges(row(tvpi=0.3, dpi=0.4)))


def test_totals_match_and_mismatch():
    funds = [row(fund_name="A", commitment=10.0), row(fund_name="B", commitment=15.0)]
    ok_total = row(fund_name="Total", commitment=25.0, contributed=200.0, distributed=80.0, nav=160.0, is_total_row=True)
    assert check_totals(funds + [ok_total]) == []
    bad_total = ok_total.model_copy(update={"commitment": 30.0})
    flags = check_totals(funds + [bad_total])
    assert reasons(flags) == ["TOTAL_MISMATCH"]
    assert flags[0].expected == 25.0


def test_agreement_flags_disagreeing_extractors():
    llm = row(source="llm", nav=80.0)
    base = row(source="baseline", nav=8.0)
    flags = check_agreement(llm, base, ["nav", "tvpi"])
    assert reasons(flags) == ["EXTRACTOR_DISAGREE"]


def test_validate_rows_skips_total_rows_for_row_checks():
    total = row(fund_name="Total", tvpi=9.9, is_total_row=True)
    assert validate_rows([total]) == []
