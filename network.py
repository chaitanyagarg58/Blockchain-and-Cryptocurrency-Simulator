import networkx as ntx
import random 
import time
import matplotlib.pyplot as plt
from typing import List


def create_network(malicious_nodes: List[int], honest_nodes: List[int], filepath: str, min_degree: int = 3, max_degree: int = 6) -> ntx.Graph:
    """
    Creates a random network with specified node count and degree constraints.

    Args:
        malicious_nodes (List[int]): List of malicious nodes in the network.
        honest_nodes (List[int]): List of honest nodes in the network.
        filepath (str): File path to save the network graph.
        min_degree (int): Minimum degree for each node.
        max_degree (int): Maximum degree for each node.

    Returns:
        Graph: A connected random graph with the specified properties.
    """
    node_ids = malicious_nodes + honest_nodes
    num_of_nodes = len(node_ids)

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
        
    Graph = ntx.relabel_nodes(Graph, node_ids.__getitem__)

    node_colors = ['black' if node in malicious_nodes else 'blue' for node in Graph.nodes()]
    ntx.draw(Graph, with_labels=True, node_color=node_colors, edge_color='gray', font_color="yellow")
    plt.savefig(filepath)
    plt.clf()

    return Graph.copy()