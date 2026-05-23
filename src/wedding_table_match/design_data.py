"""Adapter: convert our Python models into the JS-shaped object the
Floor Plan Designer prototype consumes via ``window.WEDDING_DATA``,
plus helpers to render the prototype as a single inlined HTML string.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional, Sequence

from .models import Guest, Relationship, Table

VIP_GROUP_TOKENS = {"VIP", "Bridal Party", "Wedding Party"}


def _split_name(full: str) -> tuple[str, str]:
    parts = (full or "").strip().split(" ", 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _guest_to_dict(g: Guest) -> dict:
    first, last = _split_name(g.name)
    groups = list(g.groups or [])
    return {
        "id": str(g.id),
        "name": g.name,
        "first": first,
        "last": last,
        "age": int(g.age or 0),
        "gender_identity": g.gender_identity or "",
        "rsvp": g.rsvp or "",
        "meal_preference": g.meal_preference or "",
        "single": bool(g.single),
        "plus_one": bool(g.plus_one),
        "sit_with_partner": bool(g.sit_with_partner),
        "groups": groups,
        "groupLabel": groups[0] if groups else "",
        "hobbies": list(g.hobbies or []),
        "languages": list(g.languages or []),
        "relationship_status": g.relationship_status or "",
        "location": g.location or "",
        "diet_choices": list(g.diet_choices or []),
        "partner": g.partner or "",
        "vip": any(tok in groups for tok in VIP_GROUP_TOKENS),
        "accessibility": None,
        "notes": "",
    }


def _table_to_dict(t: Table) -> dict:
    return {
        "name": t.name,
        "capacity": int(t.capacity),
        "tags": list(t.tags or []),
        "shape": "round",
    }


def _relationship_to_dict(r: Relationship) -> dict:
    return {
        "guest1_id": str(r.a),
        "guest2_id": str(r.b),
        "relationship": r.relation,
        "strength": int(r.strength or 0),
        "notes": r.notes or "",
    }


def _collect_groups(guests: Sequence[Guest]) -> List[dict]:
    seen: set[str] = set()
    out: List[dict] = []
    for g in guests:
        for key in g.groups or []:
            if key not in seen:
                seen.add(key)
                out.append({"key": key, "label": key})
    return out


def _collect_diets(guests: Sequence[Guest]) -> List[dict]:
    seen: set[str] = set()
    out: List[dict] = []
    for g in guests:
        for key in g.diet_choices or []:
            if key not in seen:
                seen.add(key)
                out.append({"key": key, "label": key})
    return out


def csv_to_wedding_data(
    guests: Sequence[Guest],
    tables: Sequence[Table],
    relationships: Sequence[Relationship],
) -> dict:
    """Build the WEDDING_DATA dict from loaded model objects."""
    initial: dict[str, str] = {}
    for g in guests:
        if getattr(g, "forced_table", "") and str(g.forced_table).strip():
            initial[str(g.id)] = str(g.forced_table).strip()

    return {
        "guests": [_guest_to_dict(g) for g in guests],
        "tables": [_table_to_dict(t) for t in tables],
        "relationships": [_relationship_to_dict(r) for r in relationships],
        "initialAssignments": initial,
        "groups": _collect_groups(guests),
        "diets": _collect_diets(guests),
    }


def wedding_data_to_js(data: dict) -> str:
    """Serialize the dict as a `window.WEDDING_DATA = {...};` assignment."""
    return f"window.WEDDING_DATA = {json.dumps(data)};"


# ---------- HTML inlining ----------

_LINK_RE = re.compile(r'<link\s+rel="stylesheet"\s+href="([^"]+)"\s*/?>')
_SCRIPT_RE = re.compile(r"<script\s+([^>]*?)>\s*</script>")


def _is_remote(src: str) -> bool:
    return src.startswith(("http://", "https://", "//"))


def render_design_html(
    html_path: Path,
    data_override: Optional[dict] = None,
) -> str:
    """Inline local CSS/JS into a single HTML string suitable for an iframe.

    If ``data_override`` is given, the prototype's ``data.js`` is replaced with
    a ``window.WEDDING_DATA = {...};`` assignment built from it. Otherwise the
    original synthetic dataset is preserved. Remote (CDN) scripts are left as
    external <script src=...> references so React/Babel still load.
    """
    base = html_path.parent
    html = html_path.read_text(encoding="utf-8")

    def replace_link(match: re.Match) -> str:
        href = match.group(1)
        if _is_remote(href):
            return match.group(0)
        return f"<style>\n{(base / href).read_text(encoding='utf-8')}\n</style>"

    html = _LINK_RE.sub(replace_link, html)

    def replace_script(match: re.Match) -> str:
        attrs = match.group(1)
        src_match = re.search(r'src="([^"]+)"', attrs)
        if not src_match:
            return match.group(0)
        src = src_match.group(1)
        if _is_remote(src):
            return match.group(0)
        type_match = re.search(r'type="([^"]+)"', attrs)
        type_attr = f' type="{type_match.group(1)}"' if type_match else ""
        if data_override is not None and src.endswith("data.js"):
            body = wedding_data_to_js(data_override)
        else:
            body = (base / src).read_text(encoding="utf-8")
        return f"<script{type_attr}>\n{body}\n</script>"

    return _SCRIPT_RE.sub(replace_script, html)
