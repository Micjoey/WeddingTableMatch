import networkx as nx
from pyvis.network import Network

def generate_assignment_mind_map(assignments, guests, relationships):
    # Build lookup for guest info
    guest_dict = {str(g.id): g for g in guests}
    # Build graph
    G = nx.Graph()
    # Add guest nodes, color by table
    table_colors = {}
    color_palette = ["#FFB347", "#77DD77", "#AEC6CF", "#C23B22", "#F49AC2", "#B39EB5", "#03C03C", "#779ECB", "#966FD6", "#FFD700"]
    # assignments: dict of guest_id -> table_name
    table_to_guests = {}
    for guest_id, table in assignments.items():
        table_to_guests.setdefault(table, []).append(guest_id)
    for idx, (table, guest_ids) in enumerate(table_to_guests.items()):
        color = color_palette[idx % len(color_palette)]
        table_colors[table] = color
        for gid in guest_ids:
            g = guest_dict.get(str(gid))
            label = g.name if g else str(gid)
            G.add_node(str(gid), label=label, table=table, color=color)
    # Add relationship edges (always add if both guests exist, even if relation is 'neutral' or strength is 0)
    for rel in relationships:
        a, b = str(rel.a).strip(), str(rel.b).strip()
        if a in G and b in G:
            edge_label = str(rel.relation) if hasattr(rel, 'relation') else ""
            if hasattr(rel, 'strength') and rel.strength:
                edge_label += f" ({rel.strength})"
            G.add_edge(a, b, label=edge_label)
    # Create pyvis network
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
    net.from_nx(G)
    # Improve physics for clarity
    net.force_atlas_2based()
    return net.generate_html()