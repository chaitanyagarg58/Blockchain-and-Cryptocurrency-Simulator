# Simulator for a P2P Cryptocurrency Network

![Python Version](https://img.shields.io/badge/python-3.8.10-blue)  

A Python-based simulator for modeling and analyzing peer-to-peer (P2P) cryptocurrency networks.
---

## Introduction

This project simulates a peer-to-peer (P2P) cryptocurrency network, allowing to model and observe various network behaviors, such as transaction propagation, block mining, forks, and consensus mechanisms.

## Environment Requirements
The simulator is built using Python 3.8.10 and relies on the following libraries:
- **`networkx`**: For network topology creation.
- **`simpy`**: For discrete-event simulation.
- **`tqdm`**: For displaying progress bars during simulations.
- **`matplotlib`**: For Vizualisation.

The library versions needed have been specifies in `requirements.txt` and can be installed using:
```
pip install -r requirements.txt
```

---

## Usage
The simulator can be run using main.py.

```
$ python3 main.py --help
usage: main.py [-h] -n NUM_PEERS -w Z0 -c Z1 -t TRANSACTION_INTERARRIVAL -b BLOCK_INTERARRIVAL -s SIM_TIME [-f FOLDER]

Process CLI Inputs.

optional arguments:
  -h, --help            show this help message and exit
  -n NUM_PEERS, --num_peers NUM_PEERS
                        Number of Peers
  -w Z0, --z0 Z0        Fraction of slow peers (0 to 1)
  -c Z1, --z1 Z1        Fraction of low CPU peers (0 to 1)
  -t TRANSACTION_INTERARRIVAL, --transaction_interarrival TRANSACTION_INTERARRIVAL
                        Mean Interarrival Time for Transaction Generation (seconds)
  -b BLOCK_INTERARRIVAL, --block_interarrival BLOCK_INTERARRIVAL
                        Mean Interarrival Time of Blocks (seconds)
  -s SIM_TIME, --sim_time SIM_TIME
                        Simulation Time (seconds)
  -f FOLDER, --folder FOLDER
                        Folder to store results
```

The `-f, --folder` parameter is not necessary and takes a default value using the other parameters.
All other parameters are necessary.

The default folder name is as follows:
```
logs_<n>_<z0 * 100>_<z1 * 100>_<t (in ms)>_<b (in ms)>_<s (in sec)>
```

---

## Output

The simulator generates the following log files:

- **`networkGraph.csv`**: Represents the network topology with the following details:  
  - `Peer 1`: One endpoint of the link  
  - `Peer 2`: The other endpoint of the link  
  - `Propagation-Delay`: Time taken for data to travel between nodes  
  - `Link Speed`: Speed of the connection between nodes  

- **`networkGraph.png`**: A visualization of the network topology based on the `networkGraph.csv` data.

- **`Node_info.csv`**: Stores information about each peer in the network, including:
  - `PeerId`: Unique identifier for each peer  
  - `CPU-Type`: Type of processor used by peer (LOW/HIGH) 
  - `Network-Type`: Connection type (SLOW/FAST)  
  - `Hashing Power`: Computational power available for mining  

- **Per-Peer Blockchain Tree Logs**
  For each peer `i`, the blockchain tree maintained by that peer is stored in `Peer_i.csv`:  
  - `BlockId`: Unique identifier for the block  
  - `ParentId`: Identifier of the parent block  
  - `creatorId`: ID of the peer that created the block  
  - `Arrival Time`: Time at which the block was received  
  - `Depth`: Position of the block in the blockchain tree  
  - `Block-Size`: Size of the block in Kilobits

