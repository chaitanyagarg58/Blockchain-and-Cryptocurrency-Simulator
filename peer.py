from enum import Enum, auto
from block import Block
from transaction import Transaction
from blockchainTree import BlockchainTree
from collections import defaultdict
import random
from typing import List

class NetworkType(Enum):
    SLOW = auto()
    FAST = auto()

class CPUType(Enum):
    LOW = auto()
    HIGH = auto()

class RepeatChecker:
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
        self.pij = {}
        self.cij = {}

        self.mempool = set()#defaultdict(Transaction)
        self.txnPropagationChecker = RepeatChecker()
        # self.blockPropogationChecker = RepeatChecker()

        self.miningBlkId = None
        # self.lastBlkId = genesisBlock.BlkID # last block id of the current longest chain considered
        self.blockchain = BlockchainTree(genesisBlock)

        self.currentBalance = 0 # Balance in the chain in the current longest chain according to this Node

    def add_connected_peer(self, connectedPeerId: int):
        self.connectedPeers.append(connectedPeerId)

    def add_txn_in_mempool(self, txn: Transaction):
        self.mempool.add(txn)
        self.txnPropagationChecker.add(txn.txnID)

    def transaction_seen(self, txn: Transaction):
        return self.txnPropagationChecker.check(txn.txnID)

    def block_seen(self, block: Block):
        return self.blockchain.check_block(block.BlkID)

    def add_propogation_link_delay(self, connectedPeerId: int, pij : float):
        self.pij[connectedPeerId] = pij

    def add_link_speed(self, connectedPeerId : int, cij : float):
        self.cij[connectedPeerId] = cij

    def add_block(self, block: Block, arrTime : float):
        self.blockchain.add_block(block, arrTime)
        longest_changed = True
        if self.blockchain.prevChainTip == self.blockchain.longestChainTip:
            longest_changed = False
        lca = self.blockchain.lca()
        insert_set = self.blockchain.get_txn_set(self.blockchain.prevChainTip, lca)
        del_set = self.blockchain.get_txn_set(self.blockchain.longestChainTip, lca)
        self.mempool = self.mempool | insert_set
        self.mempool = self.mempool.difference(del_set)
        return longest_changed

    def set_miningBlk(self, blkId: int):
        self.miningBlkId = blkId

    def mining_check(self):
        if self.miningBlkId is None:
            return True
        return self.miningBlkId != self.blockchain.longestChainTip

    def get_lastBlk(self):
        return self.blockchain.get_lastBlock()
    
    def sample_transactions(self):
        currentBalance = self.blockchain.get_lastBlock().peerBalance
        peerSpent = {peerId: 0 for peerId in currentBalance.keys()}
        txns = []

        for txn in self.mempool:
            if currentBalance[txn.senID] < peerSpent[txn.senID] + txn.amt:
                continue
            peerSpent[txn.senID] += txn.amt
            txns.append(txn)
            if len(txns) == 999:
                break
        return txns


    def log_tree(self, folder):
        self.blockchain.print_tree(filename=f"{folder}/Peer-{self.peerId}.txt")