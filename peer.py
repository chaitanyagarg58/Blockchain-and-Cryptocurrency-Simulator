from enum import Enum, auto
from block import Block
from transaction import Transaction
from blockchainTree import BlockchainTree
from collections import defaultdict

class NetworkType(Enum):
    SLOW = auto()
    FAST = auto()

class CPUType(Enum):
    LOW = auto()
    HIGH = auto()

class RepeatTransactionChecker:
    def __init__(self):
        self.threshold = 0
        self.seen = set()

    def updateThreshold(self):
        while self.threshold + 1 in self.seen:
            self.threshold += 1
            self.seen.remove(self.threshold)

    def check(self, id: int):
        return id <= self.threshold or id in self.seen
    
    def add(self, id: int):
        if self.check(id):
            return False
        
        self.seen.add(id)
        if id == self.threshold + 1:
            self.updateThreshold()
        return True

class PeerNode:
    def __init__(self, peerId: int, netType: NetworkType, cpuType: CPUType, hashingPower: float, genesisBlock: Block):
        self.peerId = peerId
        self.netType = netType
        self.cpuType = cpuType
        self.hashingPower = hashingPower
        self.connectedPeers = []

        self.mempool = defaultdict(Transaction)
        self.txnPropagationChecker = RepeatTransactionChecker()

        self.lastBlkId = genesisBlock.BlkID # last block id of the current longest chain considered
        self.blockchain = BlockchainTree(genesisBlock)

        self.currentBalance = 0 # Balance in the chain in the current longest chain according to this Node

    def add_connected_peer(self, connetedPeerId: int):
        self.connectedPeers.append(connetedPeerId)

    def add_txn_in_mempool(self, txn: Transaction):
        self.mempool[txn.txnID] = txn
        self.txnPropagationChecker.add(txn.txnID)

    def transaction_seen(self, txn: Transaction):
        return self.txnPropagationChecker.check(txn.txnID)        