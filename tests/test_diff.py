from sbedg.schema import load_schema
from sbedg.diff import diff_schemas


def test_diff_trade_v1_to_v2_reports_expected_changes():
    old = load_schema("schemas/trade_v1.json")
    new = load_schema("schemas/trade_v2.json")

    d = diff_schemas(old, new)
    out = d.pretty()

    # Must contain core changes (don’t overfit exact ordering)
    assert "Message:" in out

    assert "+ added field: venue char[4]" in out
    assert "~ changed field: qty u32 -> u64" in out
    assert "~ changed field: symbol char[8] -> char[12]" in out

    # Reorder detection: symbol moves earlier in v2.
    # Our diff pretty prints as 1-indexed positions.
    assert "↔ reordered field: symbol" in out
