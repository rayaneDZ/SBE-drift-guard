from pathlib import Path

from sbedg.schema import load_schema
from sbedg.codegen_cpp import generate_cpp


def test_codegen_emits_expected_symbols_and_types(tmp_path: Path):
    schema = load_schema("schemas/trade_v2.json")
    out_dir = tmp_path / "generated"
    paths = generate_cpp(schema, out_dir)

    h = Path(paths["h"]).read_text(encoding="utf-8")
    cpp = Path(paths["cpp"]).read_text(encoding="utf-8")

    # Header basics
    assert "struct TradeUpdate" in h
    assert "bool parse_trade_update" in h

    # Types (v2)
    assert "uint64_t ts" in h
    assert "int64_t price" in h
    assert "uint64_t qty" in h
    assert "std::array<char, 12> symbol" in h
    assert "std::array<char, 4> venue" in h

    # Cpp file includes header and has parse function
    assert '#include "trade_parser.h"' in cpp
    assert "bool parse_trade_update" in cpp

    # Ensure memcpy for char arrays appears (template behavior)
    assert "std::memcpy" in cpp
