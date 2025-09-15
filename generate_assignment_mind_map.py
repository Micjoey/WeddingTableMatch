# /Users/macallansavett/code/WeddingTableMatch/generate_assignment_mind_map.py
import math
from itertools import combinations
from typing import Dict, List, Tuple, Iterable

import networkx as nx
from pyvis.network import Network

# ---------------------------
# Public API
# ---------------------------

def generate_assignment_mind_map(
    assignments: Dict[str, str],
    guests: Iterable,
    relationships: Iterable,
    layout: str = "round",              # "round", "square", "rectangle"
    show_neutral_edges: bool = False,
    show_inter_table_edges: bool = False,
    canvas_size: Tuple[int, int] = (1600, 1000),
) -> str:
    """
    Build an interactive seating visualization.

    Parameters:
      assignments: dict of guest identifier or name to table name.
      guests: iterable of Guest dataclass.
      relationships: iterable of Relationship dataclass.
      layout: "round", "square", or "rectangle".
      show_neutral_edges: include neutral edges if True.
      show_inter_table_edges: include edges between different tables if True.
      canvas_size: width, height in pixels for layout scaling.

    Returns:
      HTML string with embedded network.
    """
    guest_by_id, id_by_name = _build_guest_lookups(guests)

    # Normalize assignment keys to guest ids
    id_assignments = {}
    for key, table in assignments.items():
        gid = str(key)
        if gid in guest_by_id:
            id_assignments[gid] = table
        elif key in id_by_name:
            id_assignments[id_by_name[key]] = table
        else:
            # Unknown key, skip
            continue

    # Group members by table
    table_to_ids: Dict[str, List[str]] = {}
    for gid, table in id_assignments.items():
        table_to_ids.setdefault(table, []).append(gid)
    for t in table_to_ids:
        table_to_ids[t].sort(key=lambda g: guest_by_id.get(g).name if guest_by_id.get(g) else g)

    # Relationship lookup
    rel_value, rel_type = _build_relationship_maps(relationships)

    # Precompute per member counts within their table
    known_neutral_neg = _compute_known_neutral_negative(table_to_ids, rel_value)

    # Coordinate system: place table centers on a grid, then seat guests around each center
    width, height = canvas_size
    centers = _compute_table_centers(list(table_to_ids.keys()), width, height)
    node_positions = _compute_seat_positions(
        table_to_ids=table_to_ids,
        centers=centers,
        layout=layout,
    )

    # Build graph
    G = nx.Graph()

    # Colors per table
    palette = [
        "#FFB347", "#77DD77", "#AEC6CF", "#C23B22", "#F49AC2", "#B39EB5",
        "#03C03C", "#779ECB", "#966FD6", "#FFD700", "#FF6961", "#CB99C9",
        "#CFCFC4", "#FDFD96", "#84B6F4", "#FDCAe1",
    ]
    table_color = {t: palette[i % len(palette)] for i, t in enumerate(sorted(table_to_ids.keys()))}

    # Nodes
    for table, member_ids in table_to_ids.items():
        for gid in member_ids:
            g = guest_by_id.get(gid)
            label = g.name if g else gid
            known, neutral, negative = known_neutral_neg.get(gid, (0, 0, 0))
            singles = getattr(g, "single", False) if g else False
            meal = getattr(g, "meal_preference", "") if g else ""
            title = _node_tooltip(label, table, singles, meal, known, neutral, negative)
            x, y = node_positions[(table, gid)]

            # Singles get a thicker border
            border_width = 4 if singles else 2

            G.add_node(
                gid,
                label=label,
                title=title,
                color=table_color[table],
                table=table,
                x=x,
                y=y,
                physics=False,
                borderWidth=border_width,
                shape="dot",
                size=18,
            )

    # Edges
    for a, b in combinations(id_assignments.keys(), 2):
        t1 = id_assignments[a]
        t2 = id_assignments[b]
        same_table = t1 == t2
        if not same_table and not show_inter_table_edges:
            continue

        v = rel_value.get((a, b))
        rtype = rel_type.get((a, b), "")
        if v is None:
            # Unknown relation, treat as neutral only if showing neutrals between tables is desired
            if not show_neutral_edges:
                continue
            v = 0

        if v == 0 and not show_neutral_edges:
            continue

        color = _edge_color(v)
        width = _edge_width(v)
        label = _edge_label(rtype, v)

        # Slight transparency for inter table edges so they do not clutter
        smooth = True if not same_table else False

        G.add_edge(a, b, color=color, width=width, label=label, smooth=smooth)

    # Build pyvis network
    net = Network(height="700px", width="100%", bgcolor="#111111", font_color="#EEEEEE")
    net.toggle_physics(False)  # positions are fixed
    net.from_nx(G)

    # Legend overlay
    _inject_legend_html(net)

    return net.generate_html()

# ---------------------------
# Internals
# ---------------------------

def _build_guest_lookups(guests) -> Tuple[Dict[str, object], Dict[str, str]]:
    guest_by_id = {}
    id_by_name = {}
    for g in guests:
        gid = str(getattr(g, "id"))
        guest_by_id[gid] = g
        id_by_name[getattr(g, "name")] = gid
    return guest_by_id, id_by_name


def _build_relationship_maps(relationships) -> Tuple[Dict[Tuple[str, str], int], Dict[Tuple[str, str], str]]:
    scale = {
        "best friend": 5,
        "friend": 3,
        "know": 2,
        "neutral": 0,
        "avoid": -3,
        "conflict": -5,
    }
    rel_value: Dict[Tuple[str, str], int] = {}
    rel_type: Dict[Tuple[str, str], str] = {}
    for r in relationships:
        a = str(getattr(r, "a")).strip()
        b = str(getattr(r, "b")).strip()
        rtype = getattr(r, "relation", "neutral")
        strength = getattr(r, "strength", None)
        val = scale.get(rtype, None)
        if val is None and isinstance(strength, int):
            val = strength
        if val is None:
            val = 0
        rel_value[(a, b)] = val
        rel_value[(b, a)] = val
        rel_type[(a, b)] = rtype
        rel_type[(b, a)] = rtype
    return rel_value, rel_type


def _compute_known_neutral_negative(table_to_ids, rel_value) -> Dict[str, Tuple[int, int, int]]:
    out: Dict[str, Tuple[int, int, int]] = {}
    for _, members in table_to_ids.items():
        for gid in members:
            known = neutral = negative = 0
            for other in members:
                if other == gid:
                    continue
                v = rel_value.get((gid, other), 0)
                if v > 0:
                    known += 1
                elif v < 0:
                    negative += 1
                else:
                    neutral += 1
            out[gid] = (known, neutral, negative)
    return out


def _compute_table_centers(tables: List[str], width: int, height: int) -> Dict[str, Tuple[int, int]]:
    """
    Place table centers on a grid inside the canvas area.
    """
    if not tables:
        return {}
    n = len(tables)
    cols = max(1, int(math.ceil(math.sqrt(n))))
    rows = int(math.ceil(n / cols))
    margin_x = 120
    margin_y = 120
    usable_w = max(1, width - 2 * margin_x)
    usable_h = max(1, height - 2 * margin_y)
    step_x = usable_w // max(1, cols)
    step_y = usable_h // max(1, rows)

    centers: Dict[str, Tuple[int, int]] = {}
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= n:
                break
            x = margin_x + c * step_x + step_x // 2
            y = margin_y + r * step_y + step_y // 2
            centers[tables[idx]] = (x, y)
            idx += 1
    return centers


def _compute_seat_positions(
    table_to_ids: Dict[str, List[str]],
    centers: Dict[str, Tuple[int, int]],
    layout: str,
) -> Dict[Tuple[str, str], Tuple[int, int]]:
    """
    Compute node coordinates per table for a chosen layout.

    round: seats on a circle.
    square: seats on a square perimeter, spill to inner ring if needed.
    rectangle: seats on a rectangle perimeter, rows longer than columns when many seats.
    """
    positions: Dict[Tuple[str, str], Tuple[int, int]] = {}
    for table, members in table_to_ids.items():
        cx, cy = centers[table]
        n = max(1, len(members))
        radius = 60 + 6 * n

        if layout == "round":
            coords = _circle_layout(cx, cy, radius, n)
        elif layout == "square":
            side = max(2, int(math.ceil(n / 4)))  # target about 4 sides
            coords = _perimeter_grid_layout(cx, cy, n, side, side)
        elif layout == "rectangle":
            # Make it wider than tall
            cols = max(3, int(math.ceil(math.sqrt(n * 2))))
            rows = max(2, int(math.ceil(n / cols)))
            coords = _perimeter_grid_layout(cx, cy, n, rows, cols)
        else:
            coords = _circle_layout(cx, cy, radius, n)

        for gid, (x, y) in zip(members, coords):
            positions[(table, gid)] = (x, y)
    return positions


def _circle_layout(cx: int, cy: int, r: int, n: int) -> List[Tuple[int, int]]:
    pts = []
    for i in range(n):
        theta = 2 * math.pi * i / n
        x = int(cx + r * math.cos(theta))
        y = int(cy + r * math.sin(theta))
        pts.append((x, y))
    return pts


def _perimeter_grid_layout(cx: int, cy: int, n: int, rows: int, cols: int) -> List[Tuple[int, int]]:
    """
    Place seats around the perimeter of a rows x cols rectangle.
    If more seats than perimeter, start an inner rectangle.
    """
    # Base rectangle size
    cell = 28
    w = cols * cell
    h = rows * cell

    def rect_points(cx, cy, w, h):
        left = cx - w // 2
        right = cx + w // 2
        top = cy - h // 2
        bottom = cy + h // 2
        pts = []
        # Top edge
        for c in range(cols):
            pts.append((left + c * cell + cell // 2, top))
        # Right edge
        for r in range(1, rows):
            pts.append((right, top + r * cell))
        # Bottom edge
        for c in range(cols - 1, -1, -1):
            pts.append((left + c * cell + cell // 2, bottom))
        # Left edge
        for r in range(rows - 1, 0, -1):
            pts.append((left, top + r * cell))
        return pts

    coords: List[Tuple[int, int]] = []
    current_w, current_h = w, h
    while len(coords) < n:
        perimeter_pts = rect_points(cx, cy, current_w, current_h)
        for p in perimeter_pts:
            if len(coords) >= n:
                break
            coords.append(p)
        # Shrink for inner ring
        current_w -= 2 * cell
        current_h -= 2 * cell
        if current_w <= cell or current_h <= cell:
            break

    # If still short, fill inside grid
    while len(coords) < n:
        coords.append((cx, cy))
    return coords


def _edge_color(value: int) -> str:
    if value > 0:
        return "#3CB371"  # positive: green
    if value < 0:
        return "#FF6B6B"  # negative: red
    return "#A9A9A9"      # neutral: gray


def _edge_width(value: int) -> int:
    v = abs(int(value))
    return 1 + min(7, v)


def _edge_label(rtype: str, value: int) -> str:
    # Keep short
    base = rtype if rtype else "neutral"
    if value != 0:
        return f"{base} ({value})"
    return base


def _node_tooltip(name: str, table: str, singles: bool, meal: str, known: int, neutral: int, negative: int) -> str:
    singles_txt = "Yes" if singles else "No"
    meal_txt = meal or "n/a"
    return (
        f"<b>{name}</b><br>"
        f"Table: {table}<br>"
        f"Single: {singles_txt}<br>"
        f"Meal: {meal_txt}<br>"
        f"Known at table: {known}<br>"
        f"Neutral at table: {neutral}<br>"
        f"Negative at table: {negative}"
    )


def _inject_legend_html(net: Network) -> None:
    css = """
    <style>
    .legend-box{
      position:absolute;right:12px;bottom:12px;
      background:#222;color:#eee;border:1px solid #444;border-radius:8px;
      padding:8px 12px;font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial;font-size:12px;
      z-index:10;
    }
    .legend-swatch{display:inline-block;width:12px;height:12px;margin-right:6px;vertical-align:middle;border:1px solid #444;}
    </style>
    """
    html = f"""
    {css}
    <div class="legend-box">
      <div><span class="legend-swatch" style="background:#3CB371"></span>positive edge</div>
      <div><span class="legend-swatch" style="background:#A9A9A9"></span>neutral edge</div>
      <div><span class="legend-swatch" style="background:#FF6B6B"></span>negative edge</div>
      <div style="margin-top:6px;">node color: table</div>
      <div>thick border: single</div>
    </div>
    """
    net.html += html
