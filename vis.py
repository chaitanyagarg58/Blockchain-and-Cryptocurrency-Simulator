#!/bin/python3
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt
import sys
import matplotlib.patches as mpatches


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


def analyze_data_in_longest_chain(G, data, n, filename):
    longest_chain = nx.dag_longest_path(G)
    low_cpu = set()
    high_cpu = set()
    slow_net = set()
    fast_net = set()
    
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

    a,b,c,d =  len(fast_net.intersection(high_cpu)), len(slow_net.intersection(high_cpu)), len (fast_net.intersection(low_cpu)), len(slow_net.intersection(low_cpu))

    total_len = len(longest_chain)
    a -= 1
    total_len -= 1
    assert a+b+c+d == total_len

    print("Total High CPU/Fast Nodes : ", len(fast_net.intersection(high_cpu)))
    print("Total High CPU/Slow Nodes : ", len(slow_net.intersection(high_cpu)))
    print("Total Low CPU/Fast Nodes :", len (fast_net.intersection(low_cpu)))
    print("Total Low CPU/Slow Nodes : ", len(slow_net.intersection(low_cpu)))

    categories = ["High CPU / Fast Net", "High CPU / Slow Net", "Low CPU / Fast Net", "Low CPU / Slow Net"]
    values = [a/total_len,b/total_len,c/total_len,d/total_len]
    colors = ["blue", "yellow", "green", "red"]  # Corresponding to given conditions

    # Plot
    plt.clf()
    plt.figure(figsize=(8, 6))
    bars = plt.bar(categories, values, color=colors)

    # Labels and title
    plt.xlabel("Categories")
    plt.ylabel("Values")
    plt.title("Bar Graph of CPU and Network Conditions")

    # Legend
    legend_labels = {
        "blue": "High CPU / Fast Net",
        "yellow": "High CPU / Slow Net",
        "green": "Low CPU / Fast Net",
        "red": "Low CPU / Slow Net"
    }
    plt.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=color) for color in legend_labels.keys()],
            labels=legend_labels.values())

    # Show plot
    plt.xticks(rotation=20)  # Rotate for better readability
    plt.savefig(f"{output_file}-stat")


if __name__ == "__main__":
    # Input and output configuration
    input_file = sys.argv[1]
    output_file = sys.argv[1].split('.')[0]
    n = int(sys.argv[2])

    # Process and visualize
    blockchain_data = parse_blockchain_file(input_file)
    G = visualize_blockchain(blockchain_data, output_file)
    analyze_data_in_longest_chain(G, blockchain_data, n, output_file)
