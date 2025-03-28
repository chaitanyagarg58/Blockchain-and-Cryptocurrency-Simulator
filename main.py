import argparse
import random
from network import create_network
from networkx import Graph as ntxGraph
from peer import PeerNode, NetworkType, CPUType
from malicious import MaliciousNode, RingMasterNode
from block import Block
from eventSimulator import run_simulation
from config import Config
import os
from typing import List, Union

def logger(peers: List[Union[PeerNode, MaliciousNode]], graph: ntxGraph, overlay_graph: ntxGraph, folder: str):
    """
    Saves the blockchain tree of each peer to the specified folder.
    
    Args:
        peers (List[Union[PeerNode, MaliciousNode]]): List of PeerNode/MaliciousNode objects.
        graph (ntxGraph): Network Topology Graph
        overlay_graph (ntxGraph): Overlay Network Topology Graph
        folder (str): Folder path where the trees will be saved.
    """
    with open(f"{folder}/Node_info.csv", "w") as file:
        file.write("PeerId, Peer-Type, CPU-Type, Network-Type, Hashing-Power\n")
        for peer in peers:
            file.write(f"{peer.peerId}, {peer.__class__.__name__}, {peer.cpuType.name}, {peer.netType.name}, {peer.hashingPower}\n")

    with open(f"{folder}/networkGraph.csv", "w") as file:
        file.write("Peer 1, Peer 2, Propagation-Delay, Link-Speed\n")
        for u, v in graph.edges():
            file.write(f"{u}, {v}, {peers[u].pij[v]:.2f}, {peers[u].cij[v]}\n")

    with open(f"{folder}/overlayGraph.csv", "w") as file:
        file.write("Peer 1, Peer 2, Propagation-Delay, Link-Speed\n")
        for u, v in overlay_graph.edges():
            file.write(f"{u}, {v}, {peers[u].overlay_pij[v]:.2f}, {peers[u].overlay_cij[v]}\n")

    for peer in peers:
        peer.log_tree(folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process CLI Inputs.")
    
    parser.add_argument("-n", "--num_honest", type=int, required=True, help="Number of Honest Peers")
    parser.add_argument("-m", "--num_malicious", type=int, required=True, help="Number of Malicious Peers")
    parser.add_argument("-o", "--timeout", type=float, required=True, help="Timeout Time (seconds)")
    parser.add_argument("-t", "--transaction_interarrival", type=float, required=True, help="Mean Interarrival Time for Transaction Generation (seconds)")
    parser.add_argument("-b", "--block_interarrival", type=float, required=True, help="Mean Interarrival Time of Blocks (seconds)")
    parser.add_argument("-s", "--sim_time", type=float, required=True, help="Simulation Time (seconds)")
    parser.add_argument("-f", "--folder", type = str, required=False, help="Folder to store results")
    parser.add_argument("-r", "--remove_eclipse", action="store_true", help="Remove Eclipse Attack from Malicous Nodes (only selfish mining)")
    parser.add_argument("-c", "--counter_measure", action="store_true", help="Remove Eclipse Attack from Malicous Nodes (only selfish mining)")
    args = parser.parse_args()

    num_honest = args.num_honest
    num_malicious = args.num_malicious
    num_peers = num_honest + num_malicious
    timeout_time = args.timeout
    transaction_interarrival_time = args.transaction_interarrival
    block_interarrival_time = args.block_interarrival
    sim_time = args.sim_time
    folder_to_store = args.folder
    Config.remove_eclipse = args.remove_eclipse
    Config.counter_measure = args.counter_measure

    if folder_to_store is None:
        folder_to_store = "."
        folder_to_store = f"logs_{num_honest}_{num_malicious}_{timeout_time}_{int(transaction_interarrival_time * 1000)}_{int(block_interarrival_time * 1000)}_{int(sim_time)}"

    os.makedirs(folder_to_store, exist_ok=True)

    # Set network, CPU types and hashing power based on given percentages
    netTypes =  [NetworkType.FAST] * num_malicious + [NetworkType.SLOW] * num_honest
    cpuTypes = [CPUType.HIGH] * (num_peers)

    hashingPowers = [10 if cpuType == CPUType.HIGH else 1 for cpuType in cpuTypes]
    hashingPowers = [hashPower / sum(hashingPowers) for hashPower in hashingPowers]

    # Initialize Block class peer IDs and create the genesis block
    Block.peerIds = list(range(num_peers))
    genesis_block = Block(creatorId=-1, txns=[], parentBlockId="-1", parentBlockBalance=None, depth=0, timestamp=0)

    # Create peers with unique IDs and properties
    malicious_peers =  [RingMasterNode(0, netTypes[0], cpuTypes[0], sum(hashingPowers[:num_malicious]), genesis_block)] + \
                    [MaliciousNode(id, netTypes[id], cpuTypes[id], 0, genesis_block) for id in range(1, num_malicious)]
    honest_peers = [PeerNode(id, netTypes[id], cpuTypes[id], hashingPowers[id], genesis_block) for id in range(num_malicious, num_peers)]
    peers = malicious_peers + honest_peers

    MaliciousNode.RingmasterId = 0

    # Generate Public Network Topology
    Graph = create_network(num_malicious, num_honest, f"{folder_to_store}/networkGraph.png")

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
    

    # Overlay Network Topology
    Overlay_Graph = create_network(num_malicious, 0, f"{folder_to_store}/overlayGraph.png")
    
    for u, v in Overlay_Graph.edges():
        peers[u].add_overlay_connected_peer(v)
        peers[v].add_overlay_connected_peer(u)
        pij = random.uniform(1, 10)
        peers[u].add_overlay_propogation_link_delay(v, pij)
        peers[v].add_overlay_propogation_link_delay(u, pij)
        cij = 100
        peers[u].add_overlay_link_speed(v, cij)
        peers[v].add_overlay_link_speed(u, cij)

    # Run the simulation with the provided parameters
    run_simulation(peers, block_interarrival_time, transaction_interarrival_time, timeout_time, sim_time)

    Config.log(folder_to_store)
    # Log required Information
    logger(peers, Graph, Overlay_Graph, folder_to_store)