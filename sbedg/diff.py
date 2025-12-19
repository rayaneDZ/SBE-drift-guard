from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .schema import MessageSchema, FieldSpec


@dataclass(frozen=True)
class DiffItem:
    kind: str
    text: str


@dataclass(frozen=True)
class SchemaDiff:
    message: str
    items: Tuple[DiffItem, ...]

    def pretty(self) -> str:
        lines = [f"Message: {self.message}"]
        if not self.items:
            lines.append("(no changes)")
            return "\n".join(lines)
        for it in self.items:
            lines.append(it.text)
        return "\n".join(lines)


def diff_schemas(old: MessageSchema, new: MessageSchema) -> SchemaDiff:
    if old.message != new.message:
        # For MVP we just note it; still diff fields independently
        msg = f"{old.message} -> {new.message}"
    else:
        msg = old.message

    old_map: Dict[str, FieldSpec] = old.field_by_name()
    new_map: Dict[str, FieldSpec] = new.field_by_name()

    old_names = old.field_names
    new_names = new.field_names

    items: List[DiffItem] = []

    # Added / removed
    for name in new_names:
        if name not in old_map:
            items.append(DiffItem("add", f"+ added field: {name} {new_map[name].type}"))
    for name in old_names:
        if name not in new_map:
            items.append(DiffItem("remove", f"- removed field: {name} {old_map[name].type}"))

    # Type / length changes
    for name in new_names:
        if name in old_map and name in new_map:
            o = old_map[name]
            n = new_map[name]
            if o.type != n.type:
                items.append(DiffItem("change", f"~ changed field: {name} {o.type} -> {n.type}"))

    # Reorder (only for common fields; ignore added/removed)
    common = [n for n in new_names if n in old_map and n in new_map]
    for name in common:
        oi = old_names.index(name)
        ni = new_names.index(name)
        if oi != ni:
            items.append(DiffItem("reorder", f"↔ reordered field: {name} ({oi+1} -> {ni+1})"))

    # Keep output stable-ish: group by kind order
    order = {"add": 0, "remove": 1, "change": 2, "reorder": 3}
    items_sorted = sorted(items, key=lambda x: (order.get(x.kind, 99), x.text))

    return SchemaDiff(message=msg, items=tuple(items_sorted))
