import os
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from sbedg.schema import load_schema
from sbedg.codegen_cpp import generate_cpp
from sbedg.fixtures import write_fixture_file


def _find_cxx():
    # Prefer g++ (CI Ubuntu), but allow clang++
    return shutil.which("g++") or shutil.which("clang++")


@pytest.mark.skipif(_find_cxx() is None, reason="No C++ compiler (g++/clang++) found on PATH")
def test_roundtrip_fixture_parsed_by_generated_cpp(tmp_path: Path):
    schema = load_schema("schemas/trade_v2.json")

    # 1) Generate C++ into temp generated dir
    gen_dir = tmp_path / "generated"
    generate_cpp(schema, gen_dir)

    # 2) Create a fixture matching schema field order (v2)
    # Note: price is i64. Scale is not applied here; we store raw integer.
    values = {
        "ts": 1700000000123,
        "symbol": "NVDA",   # will be null-padded to char[12]
        "price": 123456789, # raw i64
        "qty": 42,
        "venue": "XNAS"     # char[4]
    }
    fixture_path = tmp_path / "fixture.bin"
    write_fixture_file(schema, values, fixture_path)

    # 3) Compile: generated parser + cpp/main.cpp
    cxx = _find_cxx()
    assert cxx is not None

    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    exe = build_dir / ("parse_demo.exe" if os.name == "nt" else "parse_demo")

    cmd = [
        cxx,
        "-std=c++17",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        f"-I{gen_dir.as_posix()}",
        str(gen_dir / "trade_parser.cpp"),
        "cpp/main.cpp",
        "-o",
        str(exe),
    ]

    # Run compilation from repo root so "cpp/main.cpp" resolves
    repo_root = Path(__file__).resolve().parents[1]
    subprocess.run(cmd, check=True, cwd=repo_root)

    # 4) Execute binary on fixture
    res = subprocess.run([str(exe), str(fixture_path)], check=True, capture_output=True, text=True, cwd=repo_root)
    line = res.stdout.strip()
    assert line.startswith("{") and line.endswith("}")

    parsed = json.loads(line)

    # 5) Assert exact values
    assert parsed["ts"] == values["ts"]
    assert parsed["symbol"] == values["symbol"]
    assert parsed["price"] == values["price"]
    assert parsed["qty"] == values["qty"]
    assert parsed["venue"] == values["venue"]
