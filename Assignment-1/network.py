import networkx as ntx
import random 
import time
import matplotlib.pyplot as plt


def create_network(num_of_nodes: int, folder: str, min_degree: int = 3, max_degree: int = 6) -> ntx.Graph:
    """
    Creates a random network with specified node count and degree constraints.

    Args:
        num_of_nodes (int): Number of nodes in the network.
        min_degree (int): Minimum degree for each node.
        max_degree (int): Maximum degree for each node.

    Returns:
        Graph: A connected random graph with the specified properties.
    """

    if num_of_nodes <= max_degree: 
        max_degree = num_of_nodes - 1
    Graph = None
    while Graph is None:
        sample_degrees = [random.randint(min_degree, max_degree) for _ in range(num_of_nodes)]
        while not ntx.is_valid_degree_sequence_erdos_gallai(sample_degrees):
            sample_degrees = [random.randint(min_degree, max_degree) for _ in range(num_of_nodes)]
        
        try:
            Graph = ntx.random_degree_sequence_graph(sample_degrees, seed = 42, tries = 10)     # Fixed Seed for Deterministic Output
        except:
            continue
        
        if ntx.is_connected(Graph):
            break
        else:
            Graph = None
            continue

    ntx.draw(Graph, with_labels=True, node_color='lightblue', edge_color='gray')
    plt.savefig(f"{folder}/networkGraph.png")
    plt.clf()

    return Graph.copy()