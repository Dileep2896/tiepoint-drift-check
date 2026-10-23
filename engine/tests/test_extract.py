"""Extraction from schedule text: typed rows with source lines, bad rows reported."""

from tiepoint.extract import RuleExtractor, normalize_phase, validate_rows
from tiepoint.seed import SAMPLE_TABLE_TEXT


def test_rule_extractor_parses_sample():
    r = RuleExtractor().extract(SAMPLE_TABLE_TEXT)
    assert r.engine == "rules"
    assert len(r.rows) == 9
    assert [e.source_line for e in r.errors] == [13]
    assert "fifty" in r.errors[0].reason


def test_rows_keep_source_lines_and_values():
    rows = {x.id: x for x in RuleExtractor().extract(SAMPLE_TABLE_TEXT).rows}
    tp1 = rows["TP-01"]
    assert (tp1.stream_tag, tp1.pressure_psig, tp1.temperature_f, tp1.phase, tp1.vapor_fraction) == ("S-101", 950, 120, "V", 1.0)
    assert tp1.source_line == 3
    # page break line is skipped, so TP-05 sits on line 8
    assert rows["TP-05"].source_line == 8
    assert rows["TP-07"].description == "Contactor inlet scrubber liquids"


def test_phase_synonyms_normalised():
    rows = {x.id: x for x in RuleExtractor().extract(SAMPLE_TABLE_TEXT).rows}
    assert rows["TP-09"].phase == "L"
    assert normalize_phase("two-phase") == "2P"
    assert normalize_phase("plasma") is None


def test_unknown_phase_and_bad_vf_reported():
    text = "TP-01 S-1 gas line 10 20 PLASMA 1.0\nTP-02 S-2 wet line 10 20 V 1.7\nTP-03 S-3 short 10"
    r = RuleExtractor().extract(text)
    assert r.rows == []
    reasons = [e.reason for e in r.errors]
    assert "PLASMA" in reasons[0]
    assert "less than or equal to 1" in reasons[1]
    assert "expected" in reasons[2]


def test_numbers_with_commas():
    r = RuleExtractor().extract("TP-01 S-101 Sour gas 1,025 128 V 1.0")
    assert r.rows[0].pressure_psig == 1025


def test_llm_output_validated_like_rules():
    lines = ["header", "TP-01  S-101  Sour gas  950  120  V  1.00", "TP-02  S-102  water  65  80  L  0"]
    items = [
        {"id": "TP-01", "stream_tag": "S-101", "description": "Sour gas", "pressure_psig": 950, "temperature_f": 120, "phase": "vapor", "vapor_fraction": 1, "source_line": 2},
        {"id": "TP-02", "stream_tag": "S-102", "description": "water", "pressure_psig": None, "temperature_f": 80, "phase": "L", "vapor_fraction": 0, "source_line": 3},
        {"id": "TP-09", "stream_tag": "S-109", "description": "made up", "pressure_psig": 1, "temperature_f": 1, "phase": "L", "vapor_fraction": 0, "source_line": 3},
    ]
    rows, errors = validate_rows(items, lines)
    assert [r.id for r in rows] == ["TP-01"]
    assert rows[0].phase == "V"
    assert len(errors) == 2
    assert "not found on its cited source line" in errors[1].reason
