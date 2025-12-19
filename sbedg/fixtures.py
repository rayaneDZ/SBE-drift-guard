from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from .schema import MessageSchema


def make_fixture_bytes(schema: MessageSchema, values: Dict[str, Any]) -> bytes:
    """
    Create a binary fixture buffer for a fixed-size schema.
    MVP: little-endian only. Supports u32/u64/i64/char[N].

    values: mapping field_name -> python value
    """
    parts: list[bytes] = []
    for f in schema.fields:
        v = values.get(f.name)
        if f.type == "u32":
            if v is None:
                raise ValueError(f"Missing value for {f.name}")
            parts.append(int(v).to_bytes(4, "little", signed=False))
        elif f.type == "u64":
            if v is None:
                raise ValueError(f"Missing value for {f.name}")
            parts.append(int(v).to_bytes(8, "little", signed=False))
        elif f.type == "i64":
            if v is None:
                raise ValueError(f"Missing value for {f.name}")
            parts.append(int(v).to_bytes(8, "little", signed=True))
        elif f.is_char_array():
            n = f.char_len()
            if v is None:
                raise ValueError(f"Missing value for {f.name}")
            b = v.encode("ascii", errors="strict") if isinstance(v, str) else bytes(v)
            b = b[:n].ljust(n, b"\x00")
            parts.append(b)
        else:
            raise ValueError(f"Unsupported type: {f.type}")
    return b"".join(parts)


def write_fixture_file(schema: MessageSchema, values: Dict[str, Any], out_path: str | Path) -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(make_fixture_bytes(schema, values))
    return p
