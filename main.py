import argparse
import random
from network import create_network
from peer import PeerNode, NetworkType, CPUType
from block import Block
from eventSimulator import run_simulation
import os
from typing import List

def save_tree(peers: List['PeerNode'], folder: str):
    """
    Saves the blockchain tree of each peer to the specified folder.
    
    Args:
        peers (List[PeerNode]): List of PeerNode objects.
        folder (str): Folder path where the trees will be saved.
    """
    for peer in peers:
        peer.log_tree(folder)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process CLI Inputs.")
    
    parser.add_argument("-n", "--num_peers", type=int, required=True, help="Number of Peers")
    parser.add_argument("-w", "--z0", type=float, required=True, help="Percentage of slow peers")
    parser.add_argument("-c", "--z1", type=float, required=True, help="Percentage of low CPU peers")
    parser.add_argument("-t", "--transaction_interarrival_time", type=float, required=True, help="Mean Interarrival Time for Transaction Generation (seconds)")
    parser.add_argument("-b", "--block_interarrival_time", type=float, required=True, help="Mean Interarrival Time of Blocks (seconds)")
    parser.add_argument("-s", "--sim_time", type=float, required=True, help="Simulation Time (seconds)")
    parser.add_argument("-f", "--folder", type = str, required=False, help = "Folder to store results")
    args = parser.parse_args()

    num_peers = args.num_peers
    z0 = args.z0
    z1 = args.z1
    transaction_interarrival_time = args.transaction_interarrival_time
    block_interarrival_time = args.block_interarrival_time
    sim_time = args.sim_time
    folder_to_store = args.folder

    if folder_to_store is None:
        folder_to_store = f"{num_peers}_{z0}_{z1}_{transaction_interarrival_time}_{block_interarrival_time}_{sim_time}"

    os.makedirs(folder_to_store, exist_ok=True)

    # Set network, CPU types and hashing power based on given percentages
    netTypes = [NetworkType.SLOW] * int(z0 * num_peers) + [NetworkType.FAST] * (num_peers - int(z0 * num_peers))
    random.shuffle(netTypes)
    cpuTypes = [CPUType.LOW] * int(z1 * num_peers) + [CPUType.HIGH] * (num_peers - int(z1 * num_peers))
    random.shuffle(cpuTypes)
    hashingPowers = [10 if cpuType == CPUType.HIGH else 1 for cpuType in cpuTypes]
    hashingPowers = [hashPower / sum(hashingPowers) for hashPower in hashingPowers]

    # Initialize Block class peer IDs and create the genesis block
    Block.peerIds = list(range(num_peers))
    genesis_block = Block(creatorId=-1, txns=[], parentBlockId=-1, parentBlockBalance=None, depth=0, cpu = 1, net = 1)

    # Create peers with unique IDs and properties
    peers = [PeerNode(id, netTypes[id], cpuTypes[id], hashingPowers[id], genesis_block) for id in range(num_peers)]
    
    # Generate Network Topology
    Graph = create_network(num_peers, folder_to_store)

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
    with open(f"{folder_to_store}/Node_data.txt", "w") as file:
        file.write("PeerId,CPUType,NetworkType")
        for peer in peers:
            cpu = 0
            net = 0
            if peer.netType == NetworkType.SLOW:
                net = 0
            else:
                net = 1
            if peer.cpuType == CPUType.LOW:
                cpu = 0
            else:
                cpu = 1
            file.write(f"{peer.peerId},{cpu},{net}")
    save_tree(peers, folder_to_store)