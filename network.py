import networkx as ntx
import random 
import time
import matplotlib.pyplot as plt


def create_network(num_of_nodes, min_degree=3, max_degree=6):
    assert num_of_nodes > max_degree
    Graph = None
    while Graph is None:
        sample_degrees = [random.randint(min_degree, max_degree) for _ in range(num_of_nodes)]
        while not ntx.is_valid_degree_sequence_erdos_gallai(sample_degrees):
            sample_degrees = [random.randint(min_degree, max_degree) for _ in range(num_of_nodes)]

        Graph = ntx.random_degree_sequence_graph(sample_degrees, seed = int(time.time()), tries = 10)
        
        if len(list(ntx.selfloop_edges(Graph))) > 0 or isinstance(Graph, ntx.MultiGraph) or isinstance(Graph, ntx.MultiDiGraph):
            Graph = None

    ntx.draw(Graph, with_labels=True, node_color='lightblue', edge_color='gray')
    plt.savefig("networkGraph.png")

    return Graph