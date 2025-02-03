from enum import Enum, auto

class NetworkType(Enum):
    SLOW = auto()
    FAST = auto()

class CPUType(Enum):
    LOW = auto()
    HIGH = auto()

class PeerNode:
    def __init__(self, peerId: int, netType: NetworkType, cpuType: CPUType, hashingPower: float):
        self.peerId = peerId
        self.netType = netType
        self.cpuType = cpuType
        self.hashingPower = hashingPower
        self.connectedPeers = []
        # self.blockchain
        self.lastBlkId = 0 # last block id of the current longest chain considered

    def add_connected_peer(self, connetedPeerId):
        self.connectedPeers.append(connetedPeerId)