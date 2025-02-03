import networkx as ntx
import random 
import argparse
import time

random.seed(int(time.time()))
MIN_DEG = 3
MAX_DEG = 6

parser = argparse.ArgumentParser(description="Graph creation")
parser.add_argument("-n", "--nodes", type=int, help="Number of nodes", default=5)

args = parser.parse_args()
peers = args.nodes

MAX_DEG = min(MAX_DEG, peers-1)

G = None
while G is None:
    degree = [random.randint(MIN_DEG, MAX_DEG) for _ in range(peers)]
    try:
        correct_seq = ntx.is_valid_degree_sequence_erdos_gallai(degree)
    except:
        continue
    if correct_seq:
        try:
            G = ntx.random_degree_sequence_graph(degree, seed = int(time.time()), tries = 10)
        except:
            continue

        if ntx.is_connected(G):
            break
        else:
            G = None
            continue
    else:
        G = None
        continue

# ntx.draw(G, with_labels=True, node_color="lightblue", edge_color="gray", node_size=2000, font_size=15)

# # Show the plot
# plt.savefig("plot.png")
with open("graph_data.txt", "w") as file:
    file.write(f"{peers}\n")
    for [x,y] in G.edges():
        file.write(f"{x+1} {y+1}\n")