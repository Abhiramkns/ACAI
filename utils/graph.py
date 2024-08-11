import networkx as nx
import matplotlib.pyplot as plt


def generate_graph(nodes, edges):
    print("nodes", nodes)
    print("edges", edges)
    # Create an undirected graph
    G = nx.MultiGraph()

    l2id = {}
    for i, label in enumerate(nodes):
        # Add nodes with labels
        G.add_node(i + 1, label=label)
        l2id[label] = i + 1

    for edge in edges:
        # Add edges with labels
        G.add_edge(l2id[edge[0]], l2id[edge[1]], label=edge[2])

    # Draw the graph
    node_labels = nx.get_node_attributes(G, "label")
    # node_colors = [G.nodes[node]['color'] for node in G.nodes]

    # Draw the graph
    pos = nx.spring_layout(G)  # positions for all nodes
    nx.draw(
        G,
        pos,
        labels=node_labels,
        with_labels=True,
        edge_color="gray",
        node_size=2000,
        font_size=15,
        font_weight="bold",
    )

    # Draw edge labels for multi-edges
    edge_labels = {
        (u, v): "\n".join([d["label"] for d in G[u][v].values()]) for u, v in G.edges()
    }
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, font_size=10, font_color="red"
    )

    # Save the graph as an image file
    plt.savefig("user_info_graph.png")
