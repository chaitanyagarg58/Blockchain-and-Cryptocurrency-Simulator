from enum import Enum, auto
from block import Block
from transaction import Transaction
from blockchainTree import BlockchainTree
from collections import defaultdict
import random
from typing import List


class NetworkType(Enum):
    """Represents network speed categories."""
    SLOW = auto()
    FAST = auto()

class CPUType(Enum):
    """Represents CPU performance levels."""
    LOW = auto()
    HIGH = auto()

class RepeatChecker:
    """Efficiently tracks received messages to detect duplicates."""

    def __init__(self):
        self.threshold = 0  # The Highest ID such that all IDs below this are seen.
        self.seen = set()   # Stores out of sequence IDs

    def updateThreshold(self):
        """Advancing Threshold by removing consequetive IDs"""
        while self.threshold + 1 in self.seen:
            self.threshold += 1
            self.seen.remove(self.threshold)

    def check(self, id: int) -> bool:
        """Returns True if ID has been received before."""
        return id <= self.threshold or id in self.seen
    
    def add(self, id: int) -> bool:
        """
        Adds a new message if not seen before

        Returns:
            bool: True if the id was added, False if id was duplicate.
        """
        if self.check(id):
            return False
        
        self.seen.add(id)
        if id == self.threshold + 1:
            self.updateThreshold()
        return True


class PeerNode:
    """Represents a Peer/Miner in the blockchain P2P network."""

    def __init__(self, peerId: int, netType: NetworkType, cpuType: CPUType, hashingPower: float, genesisBlock: Block):
        """
        Initializes a PeerNode.

        Args:
            peerId (int): Unique identifier for the peer.
            netType (NetworkType): Network speed type.
            cpuType (CPUType): CPU performance type.
            hashingPower (float): Mining power of the peer.
            genesisBlock (Block): The initial block of the blockchain.
        """
        
        self.peerId = peerId
        self.netType = netType
        self.cpuType = cpuType
        self.hashingPower = hashingPower
        self.connectedPeers = []
        self.pij = {}
        self.cij = {}

        self.mempool = set()
        self.txnPropagationChecker = RepeatChecker()    # For loopless forwarding of transactions

        self.miningBlkId = None
        self.blockchain = BlockchainTree(genesisBlock)

    def add_connected_peer(self, connectedPeerId: int):
        """Add a connected peer."""
        self.connectedPeers.append(connectedPeerId)

    def add_txn_in_mempool(self, txn: Transaction):
        """Adds a transaction to the mempool and marks it as seen."""
        self.mempool.add(txn)
        self.txnPropagationChecker.add(txn.txnID)

    def transaction_seen(self, txn: Transaction) -> bool:
        """Checks if a transaction has been received before."""
        return self.txnPropagationChecker.check(txn.txnID)

    def block_seen(self, block: Block) -> bool:
        """Checks if a block has been received before."""
        return self.blockchain.check_block(block.BlkID)

    def add_propogation_link_delay(self, connectedPeerId: int, pij : float):
        """Sets the propagation delay for a connection to a peer."""
        self.pij[connectedPeerId] = pij

    def add_link_speed(self, connectedPeerId : int, cij : float):
        """Sets the link speed for a connection to a peer."""
        self.cij[connectedPeerId] = cij

    def add_block(self, block: Block, arrTime : float) -> bool:
        """
        Adds a new block to the blockchain, check for change in longest chain and updates the mempool.

        Args:
            block (Block): The new block to add.
            arrTime (float): The time the block was received.

        Returns:
            bool: True if the longest chain changed, False otherwise.
        """

        self.blockchain.add_block(block, arrTime)
        longest_changed = True
        if self.blockchain.prevChainTip == self.blockchain.longestChainTip:
            longest_changed = False
        
        # Update mempool for the longest chain
        lca = self.blockchain.lca()
        insert_set = self.blockchain.get_txn_set(self.blockchain.prevChainTip, lca)
        del_set = self.blockchain.get_txn_set(self.blockchain.longestChainTip, lca)
        self.mempool = self.mempool | insert_set
        self.mempool = self.mempool.difference(del_set)
        return longest_changed

    def set_miningBlk(self, blkId: int):
        """Updates the block ID currently being mined."""
        self.miningBlkId = blkId

    def mining_check(self) -> bool:
        """
        Checks if mining was continued till the end of the event.

        Returns:
            bool: True if mining continued, False if it stoped.
        """

        if self.miningBlkId is None:
            return True
        return self.miningBlkId != self.blockchain.longestChainTip

    def get_lastBlk(self) -> Block:
        """Returns the last block in the longest chain."""
        return self.blockchain.get_lastBlock()
    
    def sample_transactions(self) -> List['Transaction']:
        """
        Selects valid transactions from the mempool based on account balances.

        Returns:
            List[Transaction]: A list of transactions that can be included in a new block.
        """

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


    def log_tree(self, folder: str):
        """Logs the blockchain tree to a file."""
        self.blockchain.print_tree(filename=f"{folder}/Peer_{self.peerId}.txt")