#!/bin/python3
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt
import sys
import matplotlib.patches as mpatches
import numpy as np


def parse_blockchain_file(file_path):
    """Parse the blockchain data file into a dictionary"""
    blocks = {}
    with open(file_path, 'r') as f:
        lines = f.readlines()[1:]
        for line in lines:
            if line.strip():
                block_id, parent_id, creator_id, time, depth, blocksz = map(str.strip, line.split(','))
                blocks[block_id] = {
                    'parent': parent_id if parent_id != 'None' else None,
                    'creator': int(creator_id),
                    'time': time,
                    'depth': depth,
                    'blocksize' : int(blocksz)
                }
    return blocks


def get_node_data(folder):
    """Get node data from the specified folder"""
    node_data = {}
    ringmaster = None
    with open(f"{folder}/Node_info.csv", "r") as file:
        lines = file.readlines()[1:]
        for line in lines:
            if line.strip():
                peerID, peerType, cpu, net, hashingPower = map(str.strip, line.split(','))
                peerID = int(peerID)
                cpu = cpu
                net = net
                hashingPower = float(hashingPower)
                node_data[peerID] = {
                    'peerType': peerType,
                    'cpu': cpu,
                    'net': net,
                    'hashingPower': hashingPower
                }

                if peerType == "RingMasterNode":
                    ringmaster = peerID
    return ringmaster, node_data


# type is 0 for honest peer, 1 for malicious peer, 2 for ringmaster
def visualize_blockchain(node_data, data, filename, type = 0):
    T = nx.DiGraph()

    # Add edges from blockchain data
    for block in data:
        if data[block]['parent'] == "-1":
            continue
        T.add_edge(data[block]['parent'], block)

    # Set up a list to store colors
    node_colors = []
    # Assign colors to nodes based on 'cpu' and 'net' values
    for block in data:
        cId = int(data[block]['creator'])
        # net = int(data[block]['net'])

        # Determine the color for the node based on cpu and net values
        if cId == -1:
            node_colors.append('yellow')
        elif node_data[cId]['peerType'] == "PeerNode":
            node_colors.append('blue')   # 0,0 -> red
        else:
            node_colors.append('red')

    G = T 
    for u, v in G.edges():
        G[u][v]["len"] = 5.0     # Increase edge length
        G[u][v]["minlen"] = 5    # Increase minimum rank separation
        G[u][v]["weight"] = 0.01  # Lower weight to make edges longer

    if type == 2:
        title = "Ringmaster Blockchain"
    elif type == 1:
        title = "Malicious Blockchain"
    else:
        title = "Honest Blockchain"

    plt.figure(figsize=(20,10))
    pos = graphviz_layout(G, prog='dot', args='-Grankdir="LR"')

    # Draw the nodes with specified colors
    nx.draw_networkx_nodes(G, pos, node_size=200, node_color=node_colors)

    # Draw the edges with arrows
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), arrows=True, arrowstyle="<-")

    red_patch = mpatches.Patch(color='red', label='Malicious Blocks')
    # green_patch = mpatches.Patch(color='green', label='cpu=LOW, net=FAST')
    yellow_patch = mpatches.Patch(color='yellow', label='Genesis Block')
    blue_patch = mpatches.Patch(color='blue', label='Honest Blocks')
    plt.legend(handles=[red_patch, blue_patch, yellow_patch], loc='upper left')
    plt.title(title)

    # Save the figure
    plt.savefig(f"{filename}")
    return G


def analyze_data_in_longest_chain(G, data, n, filename, peerData = None):
    longest_chain = nx.dag_longest_path(G)
    # low_cpu = set()
    # high_cpu = set()
    # slow_net = set()
    # fast_net = set()
    malicious_nodes = 0
    honest_nodes = 0
    tot_malicious_nodes = 0
    tot_honest_nodes = 0

    ## finding number of nodes in the longest chain belonging to each node + each node type of creation
    nodes = {peerId:0 for peerId in range(n)}
    for i in longest_chain:
        cId = int(data[i]["creator"])
        if cId == -1:
            continue
        if peerData[cId]['peerType'] == "MaliciousNode" or peerData[cId]['peerType'] == "RingMasterNode":
            malicious_nodes += 1
        else:
            honest_nodes += 1
    
    for block in data:
        cId = int(data[block]['creator'])
        if cId == -1:
            continue
        elif peerData[cId]['peerType'] == "MaliciousNode" or peerData[cId]['peerType'] == "RingMasterNode":
            tot_malicious_nodes += 1
        else:
            tot_honest_nodes += 1

    print("Length of longest chain : ", len(longest_chain) - 1)
    print("Total malicious nodes in longest chain: ", malicious_nodes)
    print("Total honest nodes in longest chain: ", honest_nodes)
    print("Total malicous nodes in blockchain tree : ", tot_malicious_nodes)
    print("Total honest nodes in blockchain tree : ", tot_honest_nodes)


    categories = ["Malicious Nodes in longest chain", "Honest Nodes in longest chain", "Total Malicious Nodes", "Total Honest Nodes"]
    values = [malicious_nodes,honest_nodes,tot_malicious_nodes,tot_honest_nodes]
    colors = ["blue", "yellow", "green", "red"]  # Corresponding to given conditions

    plt.clf()
    plt.figure(figsize=(8, 6))
    bars = plt.bar(categories, values, color=colors)
    plt.xlabel("Categories")
    plt.ylabel("Values")
    plt.title("Bar Graph of CPU and Network Conditions")
    legend_labels = {
        "blue": "Malicious Nodes in longest chain",
        "yellow": "Honest Nodes in longest chain",
        "green": "Total Malicious Nodes",
        "red": "Total Honest Nodes"
    }
    plt.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=color) for color in legend_labels.keys()],
            labels=legend_labels.values())
    plt.xticks(rotation=20)  # Rotate for better readability
    plt.savefig(f"{filename}")
    plt.clf()

    print(f"Ratio of the number of blocks generated by malicious nodes in the longest chain at the ringmaster to the total blocks in the longest chain at the ringmaster : {malicious_nodes/(len(longest_chain) - 1)}")
    print(f"Ratio of the number of blocks generated by malicious nodes in the longest chain at the ringmaster to the total blocks generated by the malicious nodes : {malicious_nodes/tot_malicious_nodes}")



if __name__ == "__main__":
    # Input and output configuration
    folder = sys.argv[1]
    peer = None 

    if (folder[-1] == '/'):
        folder = folder[:-1]
    
    if len(sys.argv) > 2:
        peer = sys.argv[2]
        if peer != "rm":
            peer = int(peer)
    
    ringmaster, node_data = get_node_data(folder)
    n = len(node_data)
    if peer == "rm" or peer is None:
        peer = ringmaster
        type = 2
    elif node_data[peer]['peerType'] == "MaliciousNode":
        type = 1
    else:
        type = 0

    input_file = f"{folder}/Peer_{peer}.csv"
    output_file1 = f"{folder}/Peer_{peer}_blockchain.png"
    output_file2 = f"{folder}/Peer_{peer}_stat.png"
    peerData = node_data

    # # Process and visualize
    blockchain_data = parse_blockchain_file(input_file)
    G = visualize_blockchain(node_data, blockchain_data, output_file1, type)
    analyze_data_in_longest_chain(G, blockchain_data, n, output_file2, peerData)
