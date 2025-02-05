import argparse
import random
from network import create_network
from peer import PeerNode, NetworkType, CPUType
from block import Block
from eventSimulator import run_simulation

def save_tree(peers):
    for peer in peers:
        peer.log_tree()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process CLI Inputs.")
    
    parser.add_argument("-n", "--num_peers", type=int, required=True, help="Number of Peers")
    parser.add_argument("-w", "--z0", type=float, required=True, help="Percentage of slow peers")
    parser.add_argument("-c", "--z1", type=float, required=True, help="Percentage of low CPU peers")
    parser.add_argument("-t", "--transaction_mean_time", type=float, required=True, help="Mean Interarrival Time for Transaction Generation (seconds)")
    parser.add_argument("-b", "--block_interarrival_time", type=float, required=True, help="Mean Interarrival Time of Blocks (seconds)")
    parser.add_argument("-s", "--sim_time", type=int, required=True, help="Simulation Time (seconds)")

    args = parser.parse_args()

    num_peers = args.num_peers
    z0 = args.z0
    z1 = args.z1
    transaction_mean_time = args.transaction_mean_time
    block_interarrival_time = args.block_interarrival_time
    sim_time = args.sim_time

    netTypes = [NetworkType.SLOW] * int(z0 * num_peers) + [NetworkType.FAST] * (num_peers - int(z0 * num_peers))
    random.shuffle(netTypes)
    cpuTypes = [CPUType.LOW] * int(z1 * num_peers) + [CPUType.HIGH] * (num_peers - int(z1 * num_peers))
    random.shuffle(cpuTypes)
    hashingPowers = [10 if cpuType == CPUType.HIGH else 1 for cpuType in cpuTypes]
    hashingPowers = [hashPower / sum(hashingPowers) for hashPower in hashingPowers]

    Block.peerIds = list(range(num_peers))
    genesis_block = Block(creatorId=-1, txns=[], parentBlockId=-1, parentBlockBalance=None, depth=0)

    peers = [PeerNode(id, netTypes[id], cpuTypes[id], hashingPowers[id], genesis_block) for id in range(num_peers)]
    Graph = create_network(num_peers)

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

    run_simulation(peers, block_interarrival_time, transaction_mean_time, sim_time)
    save_tree(peers)