from __future__ import annotations

import argparse
from pathlib import Path

from .schema import load_schema
from .diff import diff_schemas
from .codegen_cpp import generate_cpp


def _cmd_diff(args: argparse.Namespace) -> int:
    old = load_schema(args.old)
    new = load_schema(args.new)
    d = diff_schemas(old, new)
    print(d.pretty())
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    schema = load_schema(args.schema)
    out = Path(args.out)
    paths = generate_cpp(schema, out)
    print(f"Generated:\n- {paths['h']}\n- {paths['cpp']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sbedg", description="SBE Drift Guard (1-day MVP)")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_diff = sub.add_parser("diff", help="Diff two schema JSON files")
    p_diff.add_argument("old", help="Old schema JSON path")
    p_diff.add_argument("new", help="New schema JSON path")
    p_diff.set_defaults(func=_cmd_diff)

    p_gen = sub.add_parser("generate", help="Generate C++ parser from schema")
    p_gen.add_argument("schema", help="Schema JSON path")
    p_gen.add_argument("--out", default="generated", help="Output directory (default: generated)")
    p_gen.set_defaults(func=_cmd_generate)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
