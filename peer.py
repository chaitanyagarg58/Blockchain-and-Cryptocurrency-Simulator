from enum import Enum, auto
from block import Block
from blockchainTree import BlockchainTree

class NetworkType(Enum):
    SLOW = auto()
    FAST = auto()

class CPUType(Enum):
    LOW = auto()
    HIGH = auto()

class PeerNode:
    def __init__(self, peerId: int, netType: NetworkType, cpuType: CPUType, hashingPower: float, genesisBlock: Block):
        self.peerId = peerId
        self.netType = netType
        self.cpuType = cpuType
        self.hashingPower = hashingPower
        self.connectedPeers = []
        self.lastBlkId = genesisBlock.BlkID # last block id of the current longest chain considered
        self.blockchain = BlockchainTree(genesisBlock)

    def add_connected_peer(self, connetedPeerId):
        self.connectedPeers.append(connetedPeerId)