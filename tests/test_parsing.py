import pytest

from fundx.parsing import normalise_name, parse_number, parse_percent, parse_year


@pytest.mark.parametrize(
    "text, expected",
    [
        ("1,234", 1234.0),
        ("$1,234.50", 1234.5),
        ("(12.0)", -12.0),
        ("(4.1%)", -4.1),
        ("-3.5", -3.5),
        ("-(3.5)", 3.5),
        ("1.45x", 1.45),
        ("12.5%", 12.5),
        ("USD 2,000", 2000.0),
        ("—", None),
        ("n.m.", None),
        ("", None),
        (None, None),
        ("abc", None),
        (7, 7.0),
    ],
)
def test_parse_number(text, expected):
    assert parse_number(text) == expected


def test_parse_percent_returns_fraction():
    assert parse_percent("12.5%") == pytest.approx(0.125)
    assert parse_percent("(3.1)%") == pytest.approx(-0.031)
    assert parse_percent("n/a") is None


def test_parse_year_rejects_implausible_values():
    assert parse_year("2019") == 2019
    assert parse_year("19") is None
    assert parse_year("2019.5") is None


def test_normalise_name_matches_common_variants():
    assert normalise_name("Example Partners Fund IV, L.P.") == normalise_name("example partners IV LP")
