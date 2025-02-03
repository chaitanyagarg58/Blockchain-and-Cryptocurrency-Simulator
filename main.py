import argparse
import random
from network import create_network
from peer import PeerNode, NetworkType, CPUType
from block import Block
from eventSimulator import run_simulation


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process CLI Inputs.")
    
    parser.add_argument("--num_peers", type=int, required=True, help="Number of Peers")
    parser.add_argument("--z0", type=float, required=True, help="Percentage of slow peers")
    parser.add_argument("--z1", type=float, required=True, help="Percentage of low CPU peers")
    parser.add_argument("--transaction_mean_time", type=float, required=True, help="Mean Interarrival Time for Transaction Generation (seconds)")
    parser.add_argument("--sim_time", type=int, required=True, help="Simulation Time (seconds)")

    args = parser.parse_args()

    num_peers = args.num_peers
    z0 = args.z0
    z1 = args.z1
    transaction_mean_time = args.transaction_mean_time
    sim_time = args.sim_time

    netTypes = [NetworkType.SLOW] * int(z0 * num_peers) + [NetworkType.FAST] * (num_peers - int(z0 * num_peers))
    random.shuffle(netTypes)
    cpuTypes = [CPUType.LOW] * int(z1 * num_peers) + [CPUType.HIGH] * (num_peers - int(z1 * num_peers))
    random.shuffle(cpuTypes)
    hashingPowers = [10 if cpuType == CPUType.HIGH else 1 for cpuType in cpuTypes]
    hashingPowers = [hashPower / sum(hashingPowers) for hashPower in hashingPowers]

    genesis_block = Block(-1, 1, -1, 0)

    peers = [PeerNode(id, netTypes[id], cpuTypes[id], hashingPowers[id], genesis_block) for id in range(num_peers)]
    Graph = create_network(num_peers)

    for u, v in Graph.edges():
        peers[u].add_connected_peer(v)
        peers[v].add_connected_peer(u)

    run_simulation(peers, sim_time)