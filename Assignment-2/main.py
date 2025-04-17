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

def logger(peers: List[Union[PeerNode, MaliciousNode, RingMasterNode]], graph: ntxGraph, overlay_graph: ntxGraph, folder: str):
    """
    Saves the blockchain tree of each peer to the specified folder.
    
    Args:
        peers (List[Union[PeerNode, MaliciousNode, RingMasterNode]]): List of PeerNode/MaliciousNode/RingMasterNode objects.
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
    
    parser.add_argument("-n", "--num_peers", type=int, required=True, help="Total Number of Peers")
    parser.add_argument("-m", "--ratio_malicious", type=float, required=True, help="Fraction of Malicious Peers")
    parser.add_argument("-o", "--timeout", type=float, required=True, help="Timeout Time (seconds)")
    parser.add_argument("-t", "--transaction_interarrival", type=float, required=True, help="Mean Interarrival Time for Transaction Generation (seconds)")
    parser.add_argument("-b", "--block_interarrival", type=float, required=True, help="Mean Interarrival Time of Blocks (seconds)")
    parser.add_argument("-s", "--sim_time", type=float, required=True, help="Simulation Time (seconds)")
    parser.add_argument("-f", "--folder", type = str, required=False, help="Folder to store results")
    parser.add_argument("-r", "--remove_eclipse", action="store_true", help="Remove Eclipse Attack from Malicous Nodes (only selfish mining)")
    parser.add_argument("-c", "--counter_measure", action="store_true", help="Add counter measure in Honest Nodes against eclipse attack.")
    args = parser.parse_args()

    num_peers = args.num_peers
    num_malicious = int(num_peers * args.ratio_malicious)
    num_honest = num_peers - num_malicious
    timeout_time = args.timeout
    transaction_interarrival_time = args.transaction_interarrival
    block_interarrival_time = args.block_interarrival
    sim_time = args.sim_time
    folder_to_store = args.folder
    Config.remove_eclipse = args.remove_eclipse
    Config.counter_measure = args.counter_measure

    if folder_to_store is None:
        folder_to_store = f"logs_{num_honest}_{num_malicious}_{int(timeout_time * 1000)}_{int(transaction_interarrival_time * 1000)}_{int(block_interarrival_time * 1000)}_{int(sim_time)}_{Config.remove_eclipse}_{Config.counter_measure}"

    os.makedirs(folder_to_store, exist_ok=True)

    peer_ids = list(range(num_peers))
    random.shuffle(peer_ids)

    ringmaster_id = peer_ids[0]
    malicious_ids = peer_ids[1:num_malicious]
    honest_ids = peer_ids[num_malicious:]

    # Set network, CPU types and hashing power based on given percentages
    netTypes = [NetworkType.SLOW if peer in honest_ids else NetworkType.FAST for peer in range(num_peers)]
    cpuTypes = [CPUType.HIGH] * (num_peers)

    hashingPowers = [10 if cpuType == CPUType.HIGH else 1 for cpuType in cpuTypes]
    hashingPowers = [hashPower / sum(hashingPowers) for hashPower in hashingPowers]

    hashingPowers = [power if id in honest_ids else 0 if id in malicious_ids else power * num_malicious for id, power in enumerate(hashingPowers)]

    # Initialize Block class peer IDs and create the genesis block
    Block.peerIds = peer_ids
    genesis_block = Block(creatorId=-1, txns=[], parentBlockId="-1", parentBlockBalance=None, depth=0, timestamp=0)

    MaliciousNode.RingmasterId = ringmaster_id

    # Create peers with unique IDs and properties
    malicious_peers =  [RingMasterNode(ringmaster_id, netTypes[ringmaster_id], cpuTypes[ringmaster_id], hashingPowers[ringmaster_id], genesis_block)] + \
                    [MaliciousNode(id, netTypes[id], cpuTypes[id], hashingPowers[id], genesis_block) for id in malicious_ids]
    honest_peers = [PeerNode(id, netTypes[id], cpuTypes[id], hashingPowers[id], genesis_block) for id in honest_ids]
    peers = malicious_peers + honest_peers
    peers.sort(key=lambda x: x.peerId)

    # Generate Public Network Topology
    Graph = create_network([ringmaster_id] + malicious_ids, honest_ids, f"{folder_to_store}/networkGraph.png")

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
    Overlay_Graph = create_network([ringmaster_id] + malicious_ids, [], f"{folder_to_store}/overlayGraph.png")
    
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