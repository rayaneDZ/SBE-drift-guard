from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, PackageLoader

from .schema import MessageSchema


def _cpp_ident(s: str) -> str:
    # MVP: assume schema message names are safe identifiers
    return s


def generate_cpp(schema: MessageSchema, out_dir: str | Path) -> Dict[str, Path]:
    """
    Render C++ parser files from Jinja templates into out_dir.

    Returns dict of output paths: {"h": Path(...), "cpp": Path(...)}
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Fixed naming for MVP
    header_filename = "trade_parser.h"
    cpp_filename = "trade_parser.cpp"

    struct_name = _cpp_ident(schema.message)
    parser_fn = "parse_trade_update"
    guard = f"{struct_name.upper()}_PARSER_H"

    fields = [f.to_cpp() for f in schema.fields]
    total_size = schema.total_wire_size()

    env = Environment(
        loader=PackageLoader("sbedg", "templates"),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    h_tpl = env.get_template("parser.h.j2")
    cpp_tpl = env.get_template("parser.cpp.j2")

    h_text = h_tpl.render(
        guard=guard,
        struct_name=struct_name,
        parser_fn=parser_fn,
        fields=fields,
        total_size=total_size,
    )

    cpp_text = cpp_tpl.render(
        header_filename=header_filename,
        struct_name=struct_name,
        parser_fn=parser_fn,
        fields=fields
    )

    h_path = out / header_filename
    cpp_path = out / cpp_filename

    h_path.write_text(h_text, encoding="utf-8")
    cpp_path.write_text(cpp_text, encoding="utf-8")

    return {"h": h_path, "cpp": cpp_path}
