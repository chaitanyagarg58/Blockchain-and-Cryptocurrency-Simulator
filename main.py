import argparse
import random
from network import create_network
from networkx import Graph as ntxGraph
from peer import PeerNode, NetworkType, CPUType
from malicious import MaliciousNode
from block import Block
from eventSimulator import run_simulation
import os
from typing import List

def logger(peers: List['PeerNode'], graph: ntxGraph,  folder: str):
    """
    Saves the blockchain tree of each peer to the specified folder.
    
    Args:
        peers (List[PeerNode]): List of PeerNode objects.
        folder (str): Folder path where the trees will be saved.
    """
    with open(f"{folder}/Node_info.csv", "w") as file:
        file.write("PeerId, CPU-Type, Network-Type, Hashing-Power\n")
        for peer in peers:
            file.write(f"{peer.peerId}, {peer.cpuType.name}, {peer.netType.name}, {peer.hashingPower}\n")

    with open(f"{folder}/networkGraph.csv", "w") as file:
        file.write("Peer 1, Peer 2, Propagation-Delay, Link-Speed\n")
        for u, v in graph.edges():
            file.write(f"{u}, {v}, {peers[u].pij[v]:.2f}, {peers[u].cij[v]}\n")

    for peer in peers:
        peer.log_tree(folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process CLI Inputs.")
    
    parser.add_argument("-n", "--num_honest", type=int, required=True, help="Number of Honest Peers")
    parser.add_argument("-m", "--num_malicious", type=int, required=True, help="Number of Malicious Peers")
    # parser.add_argument("-w", "--z0", type=float, required=True, help="Fraction of slow peers (0 to 1)")
    # parser.add_argument("-c", "--z1", type=float, required=True, help="Fraction of low CPU peers (0 to 1)")
    parser.add_argument("-t", "--transaction_interarrival", type=float, required=True, help="Mean Interarrival Time for Transaction Generation (seconds)")
    parser.add_argument("-b", "--block_interarrival", type=float, required=True, help="Mean Interarrival Time of Blocks (seconds)")
    parser.add_argument("-s", "--sim_time", type=float, required=True, help="Simulation Time (seconds)")
    parser.add_argument("-f", "--folder", type = str, required=False, help = "Folder to store results")
    args = parser.parse_args()

    num_honest = args.num_honest
    num_malicious = args.num_malicious
    num_peers = num_honest + num_malicious
    # z0 = args.z0
    # z1 = args.z1
    transaction_interarrival_time = args.transaction_interarrival
    block_interarrival_time = args.block_interarrival
    sim_time = args.sim_time
    folder_to_store = args.folder

    if folder_to_store is None:
        folder_to_store = "."
        folder_to_store = f"logs_{num_honest}_{num_malicious}_{int(transaction_interarrival_time * 1000)}_{int(block_interarrival_time * 1000)}_{int(sim_time)}"

    os.makedirs(folder_to_store, exist_ok=True)

    # Set network, CPU types and hashing power based on given percentages
    netTypes = [NetworkType.SLOW] * num_honest + [NetworkType.FAST] * num_malicious
    cpuTypes = [CPUType.HIGH] * (num_peers)

    hashingPowers = [10 if cpuType == CPUType.HIGH else 1 for cpuType in cpuTypes]
    hashingPowers = [hashPower / sum(hashingPowers) for hashPower in hashingPowers]

    # Initialize Block class peer IDs and create the genesis block
    Block.peerIds = list(range(num_peers))
    genesis_block = Block(creatorId=-1, txns=[], parentBlockId=-1, parentBlockBalance=None, depth=0)

    # Create peers with unique IDs and properties
    # peers = [PeerNode(id, netTypes[id], cpuTypes[id], hashingPowers[id], genesis_block) for id in range(num_peers)]


    peers = [PeerNode(id, NetworkType.SLOW, cpuTypes[id], hashingPowers[id], genesis_block) for id in range(num_honest)] + \
            [MaliciousNode(id, NetworkType.FAST, cpuTypes[id], hashingPowers[id], genesis_block) for id in range(num_honest, num_peers)]
    
    # Generate Network Topology
    Graph = create_network(num_honest, num_malicious, folder_to_store)

    # Add network links, propagation delays, and link speeds between connected peers
    for u, v in Graph.edges():
        peers[u].add_connected_peer(v)
        peers[v].add_connected_peer(u)
        pij = random.uniform(10, 500)
        peers[u].add_propogation_link_delay(v, pij)
        peers[v].add_propogation_link_delay(u, pij)
        cij = 5
        if peers[u].netType is NetworkType.FAST and peers[v].netType is NetworkType.FAST:
            cij = 100
        peers[u].add_link_speed(v, cij)
        peers[v].add_link_speed(u, cij)
    

    # Run the simulation with the provided parameters
    run_simulation(peers, block_interarrival_time, transaction_interarrival_time, sim_time)

    # Log required Information
    logger(peers, Graph, folder_to_store)