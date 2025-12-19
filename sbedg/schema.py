from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any, Dict, List, Optional, Tuple


_CHAR_RE = re.compile(r"^char\[(\d+)\]$")


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str                    # e.g. "u64", "i64", "char[12]"
    scale: Optional[int] = None  # accepted but not used in parsing

    def is_char_array(self) -> bool:
        return _CHAR_RE.match(self.type) is not None

    def char_len(self) -> int:
        m = _CHAR_RE.match(self.type)
        if not m:
            raise ValueError(f"Not a char[N] type: {self.type}")
        return int(m.group(1))

    def wire_size(self) -> int:
        if self.type == "u32":
            return 4
        if self.type == "u64":
            return 8
        if self.type == "i64":
            return 8
        if self.is_char_array():
            return self.char_len()
        raise ValueError(f"Unsupported field type: {self.type}")

    def to_cpp(self) -> Dict[str, Any]:
        """
        Convert to a dict for templating:
        - kind: "int" or "char_array"
        - cpp_type: uint32_t/uint64_t/int64_t or std::array<char,N>
        """
        if self.type == "u32":
            return {"name": self.name, "kind": "int", "cpp_type": "uint32_t"}
        if self.type == "u64":
            return {"name": self.name, "kind": "int", "cpp_type": "uint64_t"}
        if self.type == "i64":
            return {"name": self.name, "kind": "int", "cpp_type": "int64_t"}
        if self.is_char_array():
            n = self.char_len()
            return {"name": self.name, "kind": "char_array", "cpp_type": f"std::array<char, {n}>", "n": n}
        raise ValueError(f"Unsupported field type: {self.type}")


@dataclass(frozen=True)
class MessageSchema:
    message: str
    endianness: str
    fields: Tuple[FieldSpec, ...]

    @property
    def field_names(self) -> List[str]:
        return [f.name for f in self.fields]

    def field_by_name(self) -> Dict[str, FieldSpec]:
        return {f.name: f for f in self.fields}

    def total_wire_size(self) -> int:
        return sum(f.wire_size() for f in self.fields)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def load_schema(path: str | Path) -> MessageSchema:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    _require(isinstance(data, dict), "Schema must be a JSON object.")
    message = data.get("message")
    endianness = data.get("endianness", "little")
    fields = data.get("fields")

    _require(isinstance(message, str) and message.strip(), "Schema must have non-empty 'message' string.")
    _require(endianness == "little", "Only endianness='little' is supported in this MVP.")
    _require(isinstance(fields, list) and len(fields) > 0, "Schema must have non-empty 'fields' list.")

    parsed: List[FieldSpec] = []
    seen = set()
    for i, f in enumerate(fields):
        _require(isinstance(f, dict), f"Field at index {i} must be an object.")
        name = f.get("name")
        typ = f.get("type")
        scale = f.get("scale")

        _require(isinstance(name, str) and name.strip(), f"Field at index {i} missing/invalid 'name'.")
        _require(isinstance(typ, str) and typ.strip(), f"Field '{name}' missing/invalid 'type'.")

        _require(name not in seen, f"Duplicate field name: {name}")
        seen.add(name)

        if scale is not None:
            _require(isinstance(scale, int), f"Field '{name}' scale must be int if provided.")

        fs = FieldSpec(name=name, type=typ, scale=scale)
        # Validate supported type
        _ = fs.wire_size()
        parsed.append(fs)

    return MessageSchema(message=message, endianness=endianness, fields=tuple(parsed))
