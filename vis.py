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
                block_id, parent_id, creator_id, time, cpu, net, blocksz = map(str.strip, line.split(','))
                blocks[block_id] = {
                    'parent': parent_id if parent_id != 'None' else None,
                    'creator': creator_id,
                    'time': time,
                    'cpu' : cpu,
                    'net' : net,
                    'blocksize' : int(blocksz)
                }
    return blocks


# def visualize_blockchain(data, filename):
#     T = nx.Graph()

#     # for a, b in zip(file.id, file.pid):
#     #     if( a < 150 and b < 150 and a >= 0 and b >= 0):
#     #         T.add_edge(b, a)

#     for block in data:
#         T.add_edge(int(data[block]['parent']), int(block))

#     G = T 
#     title = filename #get_title_from_filename_as_dict(filename)
#     plt.figure(figsize=(20,10))
#     pos = graphviz_layout(G, prog='dot', args='-Grankdir="LR"')
#     nx.draw_networkx_nodes(G, pos, node_size=300)
#     nx.draw_networkx_edges(G, pos, edgelist=G.edges(), arrows=True, arrowstyle="<-")
#     plt.savefig(f"{filename}")


def visualize_blockchain(data, filename):
    T = nx.DiGraph()

    # Add edges from blockchain data
    for block in data:
        if int(data[block]['parent']) == -1:
            continue
        T.add_edge(int(data[block]['parent']), int(block))

    # Set up a list to store colors
    node_colors = []
    # Assign colors to nodes based on 'cpu' and 'net' values
    for block in data:
        cpu = int(data[block]['cpu'])
        net = int(data[block]['net'])
        if block == 0:
            print(cpu, net)
        # Determine the color for the node based on cpu and net values
        if cpu == 0 and net == 0:
            node_colors.append('red')   # 0,0 -> red
        elif cpu == 0 and net == 1:
            node_colors.append('green') # 0,1 -> green
        elif cpu == 1 and net == 1:
            node_colors.append('blue')  # 1,0 -> blue
        elif cpu == 1 and net == 0:
            node_colors.append('yellow') # 1,1 -> yellow

    G = T 

    title = filename  
    plt.figure(figsize=(20,10))
    pos = graphviz_layout(G, prog='dot', args='-Grankdir="LR"')

    # Draw the nodes with specified colors
    nx.draw_networkx_nodes(G, pos, node_size=300, node_color=node_colors)

    # Draw the edges with arrows
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), arrows=True, arrowstyle="<-")

    red_patch = mpatches.Patch(color='red', label='cpu=LOW, net=SLOW')
    green_patch = mpatches.Patch(color='green', label='cpu=LOW, net=FAST')
    yellow_patch = mpatches.Patch(color='yellow', label='cpu=HIGH, net=SLOW')
    blue_patch = mpatches.Patch(color='blue', label='cpu=HIGH, net=FAST')
    plt.legend(handles=[red_patch, green_patch, blue_patch, yellow_patch])

    # Save the figure
    plt.savefig(f"{filename}")
    return G


def analyze_data_in_longest_chain(G, data, n, filename, peerData = None):
    fast_net_peer = set()
    slow_net_peer = set()
    high_cpu_peer = set()
    low_cpu_peer = set()
    # peers = {peerId:0 for peerId in range(n)} # 0 for CPU/NEt 1 for CPU 2 for Net 3 for None
    with open(peerData, "r") as file:
        lines = file.readlines()[1:]
        for line in lines:
            if line.strip():
                peerID, cpu, net = map(str.strip, line.split(','))
                peerID = int(peerID)
                cpu = int(cpu)
                net = int(net)
                if cpu == 1:
                    high_cpu_peer.add(peerID)
                else:
                    low_cpu_peer.add(peerID)
                
                if net == 1:
                    fast_net_peer.add(peerID)
                else:
                    slow_net_peer.add(peerID)    
    
    
    longest_chain = nx.dag_longest_path(G)
    low_cpu = set()
    high_cpu = set()
    slow_net = set()
    fast_net = set()
    
    ## finding number of nodes in the longest chain belonging to each node + each node type of creation
    nodes = {peerId:0 for peerId in range(n)}
    for i in longest_chain:
        if data[str(i)]["cpu"] == "1":
            high_cpu.add(i)
        else:
            low_cpu.add(i)
        
        if data[str(i)]["creator"] != "-1":
            nodes[int(data[str(i)]["creator"])] += 1
        
        if data[str(i)]["net"] == "1":
            fast_net.add(i)
        else:
            slow_net.add(i)

    numForks = 0
    for i in G.nodes():
        if G.out_degree(i) > 1:
            numForks += G.out_degree(i) - 1
    print ("Total Number of Blocks Mined :", len(data))
    print("Length of longest chain : ", len(longest_chain) - 1)
    print("Number of Forks : ", numForks)
    print("Total high CPU nodes : ", len(high_cpu) - 1)
    print("Total low CPU nodes : ", len(low_cpu))
    print("Total fast net nodes : ", len(fast_net) - 1)
    print("Total slow net nodes : ", len(slow_net))

    a,b,c,d =  len(fast_net.intersection(high_cpu)), len(slow_net.intersection(high_cpu)), len (fast_net.intersection(low_cpu)), len(slow_net.intersection(low_cpu))

    total_len = len(longest_chain)
    a -= 1
    total_len -= 1

    a /= len(fast_net_peer.intersection(high_cpu_peer))
    b /= len(slow_net_peer.intersection(high_cpu_peer))
    c /= len(fast_net_peer.intersection(low_cpu_peer))
    d /= len(slow_net_peer.intersection(low_cpu_peer))

    print("Total High CPU/Fast Nodes : ", a)
    print("Total High CPU/Slow Nodes : ", b)
    print("Total Low CPU/Fast Nodes :", c)
    print("Total Low CPU/Slow Nodes : ", d)

    categories = ["High CPU / Fast Net", "High CPU / Slow Net", "Low CPU / Fast Net", "Low CPU / Slow Net"]
    values = [a/total_len,b/total_len,c/total_len,d/total_len]
    colors = ["blue", "yellow", "green", "red"]  # Corresponding to given conditions

    sys.__stdout__.write("Longest Chain Contribution:\n")
    sys.__stdout__.write(f"{a}, {b}, {c}, {d}\n")
    sys.__stdout__.write(f"{total_len}\n")
    sys.__stdout__.flush()

    plt.clf()
    plt.figure(figsize=(8, 6))
    bars = plt.bar(categories, values, color=colors)
    plt.xlabel("Categories")
    plt.ylabel("Contribution per Node")
    plt.title("Contribution per Node in the longest chain")
    legend_labels = {
        "blue": "High CPU / Fast Net",
        "yellow": "High CPU / Slow Net",
        "green": "Low CPU / Fast Net",
        "red": "Low CPU / Slow Net"
    }
    plt.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=color) for color in legend_labels.keys()],
            labels=legend_labels.values())
    plt.xticks(rotation=20)  # Rotate for better readability
    plt.savefig(f"{filename}-longest-chain-contribution")
    plt.clf()

    low_cpu_total = set()
    high_cpu_total = set()
    slow_net_total = set()
    fast_net_total = set()
    for i in G.nodes():
        if data[str(i)]["cpu"] == "1":
            high_cpu_total.add(i)
        else:
            low_cpu_total.add(i)

        if data[str(i)]["net"] == "1":
            fast_net_total.add(i)
        else:
            slow_net_total.add(i)

    a,b,c,d =  len(fast_net_total.intersection(high_cpu_total)), len(slow_net_total.intersection(high_cpu_total)), len (fast_net_total.intersection(low_cpu_total)), len(slow_net_total.intersection(low_cpu_total))

    total_len = len(G.nodes())
    a -= 1
    total_len -= 1

    a /= len(fast_net_peer.intersection(high_cpu_peer))
    b /= len(slow_net_peer.intersection(high_cpu_peer))
    c /= len(fast_net_peer.intersection(low_cpu_peer))
    d /= len(slow_net_peer.intersection(low_cpu_peer))

    categories = ["High CPU / Fast Net", "High CPU / Slow Net", "Low CPU / Fast Net", "Low CPU / Slow Net"]
    values = [a/total_len,b/total_len,c/total_len,d/total_len]
    colors = ["blue", "yellow", "green", "red"]  # Corresponding to given conditions

    sys.__stdout__.write("Total Tree Contribution:\n")
    sys.__stdout__.write(f"{a}, {b}, {c}, {d}\n")
    sys.__stdout__.write(f"{total_len}\n")
    sys.__stdout__.flush()

    plt.clf()
    plt.figure(figsize=(8, 6))
    bars = plt.bar(categories, values, color=colors)
    plt.xlabel("Categories")
    plt.ylabel("Contribution per Node")
    plt.title("Contribution per Node in the complete tree")
    legend_labels = {
        "blue": "High CPU / Fast Net",
        "yellow": "High CPU / Slow Net",
        "green": "Low CPU / Fast Net",
        "red": "Low CPU / Slow Net"
    }
    plt.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=color) for color in legend_labels.keys()],
            labels=legend_labels.values())
    plt.xticks(rotation=20)  # Rotate for better readability
    plt.savefig(f"{filename}-total-contribution")
    plt.clf()



    a,b,c,d =  len(fast_net.intersection(high_cpu)), len(slow_net.intersection(high_cpu)), len (fast_net.intersection(low_cpu)), len(slow_net.intersection(low_cpu))

    a -= 1

    e = a + b
    f = c + d
    sys.__stdout__.write(f"{a}, {b}, {c}, {d}, {e}, {f}\n")

    a /= (len(fast_net_total.intersection(high_cpu_total)) - 1)
    b /= len(slow_net_total.intersection(high_cpu_total))
    c /= len(fast_net_total.intersection(low_cpu_total))
    d /= len(slow_net_total.intersection(low_cpu_total))

    e /= (len(fast_net_total.intersection(high_cpu_total)) - 1) + len(slow_net_total.intersection(high_cpu_total))
    f /= len(fast_net_total.intersection(low_cpu_total)) + len(slow_net_total.intersection(low_cpu_total))

    categories = ["High CPU / Fast Net", "High CPU / Slow Net", "Low CPU / Fast Net", "Low CPU / Slow Net"]
    values = [a,b,c,d]
    colors = ["blue", "yellow", "green", "red"]  # Corresponding to given conditions

    sys.__stdout__.write("Efficiency Contribution:\n")
    sys.__stdout__.write(f"{a}, {b}, {c}, {d}, {e}, {f}\n")
    sys.__stdout__.flush()

    plt.clf()
    plt.figure(figsize=(8, 6))
    bars = plt.bar(categories, values, color=colors)
    plt.xlabel("Categories")
    plt.ylabel("Values")
    plt.title("Bar Graph of CPU and Network Conditions")
    legend_labels = {
        "blue": "High CPU / Fast Net",
        "yellow": "High CPU / Slow Net",
        "green": "Low CPU / Fast Net",
        "red": "Low CPU / Slow Net"
    }
    plt.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=color) for color in legend_labels.keys()],
            labels=legend_labels.values())
    plt.xticks(rotation=20)  # Rotate for better readability
    plt.savefig(f"{filename}-Efficiency")
    plt.clf()





    
    ## finding number of nodes in the longest chain belonging to each node + each node type of creation
    nodes = {peerId:0 for peerId in range(n)}
    for i in longest_chain:
        if data[str(i)]["cpu"] == "1":
            high_cpu.add(i)
        else:
            low_cpu.add(i)
        
        if data[str(i)]["creator"] != "-1":
            nodes[int(data[str(i)]["creator"])] += 1
        
        if data[str(i)]["net"] == "1":
            fast_net.add(i)
        else:
            slow_net.add(i)







    ## finding nodes in the tree belonging to each peer
    nodes_tree = {peerId:0 for peerId in range(n)}
    low_cpu_tree = set()
    high_cpu_tree = set()
    slow_net_tree = set()
    fast_net_tree = set()
    for x in data:
        i = int(x)
        if data[str(i)]["cpu"] == "1":
            high_cpu_tree.add(i)
        else:
            low_cpu_tree.add(i)
        
        if data[str(i)]["creator"] != "-1":
            nodes_tree[int(data[str(i)]["creator"])] += 1
        
        if data[str(i)]["net"] == "1":
            fast_net_tree.add(i)
        else:
            slow_net_tree.add(i)
    
    ## Finding Ratio of Nodes in longest chain vs whole tree for all nodes
    ratio_peer_nodes = {peerId:0 for peerId in range(n)}
    for i in range(n):
        if nodes_tree[i] == 0:
            ratio_peer_nodes[i] = 0
        else:
            ratio_peer_nodes[i] = nodes[i]/nodes_tree[i] 
    
    peers = {peerId:0 for peerId in range(n)} # 0 for CPU/NEt 1 for CPU 2 for Net 3 for None
    with open(peerData, "r") as file:
        lines = file.readlines()[1:]
        for line in lines:
            if line.strip():
                peerID, cpu, net = map(str.strip, line.split(','))
                peerID = int(peerID)
                cpu = int(cpu)
                net = int(net)
                if cpu == 1 and net == 1:
                    peers[peerID] = 0
                elif cpu == 1:
                    peers[peerID] = 1
                elif net == 1:
                    peers[peerID] = 2
                else:
                    peers[peerID] = 3
    grouped_data = {dtype:[] for dtype in range(4)}
    for key,value in ratio_peer_nodes.items():
        dtype = peers[key]
        if value == -1:
            continue
        grouped_data[dtype].append(value)

    for i in range(4):
        if not grouped_data[i]:
            grouped_data[i].append(0)

    med_val = 50
    print("Median for Fast/High : ", f"{np.percentile(grouped_data[0], med_val):.2f}")
    print("Median for Slow/High : ", f"{np.percentile(grouped_data[1], med_val):.2f}")
    print("Median for Fast/Low : ", f"{np.percentile(grouped_data[2], med_val):.2f}")
    print("Median for Slow/Low : ", f"{np.percentile(grouped_data[3], med_val):.2f}")

    print("Mean for Fast/High : ", f"{np.mean(grouped_data[0]):.2f}")
    print("Mean for Slow/High : ", f"{np.mean(grouped_data[1]):.2f}")
    print("Mean for Fast/Low : ", f"{np.mean(grouped_data[2]):.2f}")
    print("Mean for Slow/Low : ", f"{np.mean(grouped_data[3]):.2f}")

    # print("90th for Fast/High : ", f"{np.percentile(grouped_data[0],90):.2f}")
    # print("90th for Slow/High : ", f"{np.percentile(grouped_data[1],90):.2f}")
    # print("90th for Fast/Low : ", f"{np.percentile(grouped_data[2],90):.2f}")
    # print("90th for Slow/Low : ", f"{np.percentile(grouped_data[3],90):.2f}")

    # x = list(ratio_peer_nodes.keys())
    # y = list(ratio_peer_nodes.values())
    # plt.figure(figsize=(8, 5))
    # plt.plot(x, y, marker='o', linestyle='-', color='b', label="Values")
    # plt.xlabel("PeerID")
    # plt.ylabel("Ratio")
    # plt.title("Ratio Peer Nodes in Longest Chain vs Total Tree")
    # plt.legend()
    # plt.grid(True)
    # plt.savefig("ratio_peer_chains")
    
    ## Finding the number of branches int the tree and number of branch_nodes
    num_chain_nodes = len(longest_chain)
    num_tree_nodes = len(data)
    num_branch_nodes = num_tree_nodes - num_chain_nodes
    outgoing_edges_count = {node: G.out_degree(node) for node in G.nodes()}
    branches = 0
    for x in outgoing_edges_count:
        if x not in longest_chain:
            continue
        if outgoing_edges_count[x] > 1:
            branches += outgoing_edges_count[x]-1
    print(branches, num_branch_nodes)
    print(f"Number of blockchain nodes per branch : {num_branch_nodes/branches :.2f}")


if __name__ == "__main__":
    # Input and output configuration
    folder = sys.argv[1]
    if (folder[-1] == '/'):
        folder = folder[:-1]
    
    input_file = f"{folder}/Peer_0.txt"
    output_file = f"{folder}/Peer_0"
    peerData = f"{folder}/Node_data.txt"
    n = int(folder.split("_")[1])

    sys.stdout = open(f"{output_file}-log.txt", "w")
    # Process and visualize
    blockchain_data = parse_blockchain_file(input_file)
    G = visualize_blockchain(blockchain_data, output_file)
    analyze_data_in_longest_chain(G, blockchain_data, n, output_file, peerData)
