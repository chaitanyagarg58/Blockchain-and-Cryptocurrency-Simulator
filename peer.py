from enum import Enum, auto
from block import Block
from transaction import Transaction
from blockchainTree import BlockchainTree
from collections import deque
from dataclasses import dataclass, field
import random
from typing import List, Deque, Optional


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

@dataclass
class BlockHashMetadata:
    all_senders: List[int] = field(default_factory=list) # list of all senders (including those who timedout)
    senders: Deque[int] = field(default_factory=deque)  # Peers who sent this hash
    timeout_active: bool = False  # Whether a timeout is running

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

        self.receivedHashes: dict[str, BlockHashMetadata] = {} 

        self.miningBlkId = None
        self.blockchain = BlockchainTree(genesisBlock)

    def add_connected_peer(self, connectedPeerId: int):
        """Add a connected peer."""
        self.connectedPeers.append(connectedPeerId)

    def add_propogation_link_delay(self, connectedPeerId: int, pij : float):
        """Sets the propagation delay for a connection to a peer."""
        self.pij[connectedPeerId] = pij

    def add_link_speed(self, connectedPeerId : int, cij : float):
        """Sets the link speed for a connection to a peer."""
        self.cij[connectedPeerId] = cij

    def add_txn_in_mempool(self, txn: Transaction):
        """Adds a transaction to the mempool and marks it as seen."""
        self.mempool.add(txn)
        self.txnPropagationChecker.add(txn.txnID)

    def transaction_seen(self, txn: Transaction) -> bool:
        """Checks if a transaction has been received before."""
        return self.txnPropagationChecker.check(txn.txnID)

    def block_seen(self, blkId: str) -> bool:
        """Checks if a block has been received before."""
        return self.blockchain.check_block(blkId)

    def add_hash(self, blkId: str, senderId: int) -> bool:
        """
        Adds a block hash to the received Hashes.
        
        Args:
            blkId (str): The hash of the block.
        
        Returns:
            bool: True if a new get request (and timeout) should be created for this sender right now, False otherwise.
        """
        if blkId not in self.receivedHashes:
            self.receivedHashes[blkId] = BlockHashMetadata()

        self.receivedHashes[blkId].senders.append(senderId)
        self.receivedHashes[blkId].all_senders.append(senderId)
        return not self.receivedHashes[blkId].timeout_active
    
    def set_active_timeout(self, blkId: str):
        """Set the timeout for given blkId as active"""
        self.receivedHashes[blkId].timeout_active = True
    
    def get_block_for_get_request(self, blkId: str) -> Optional[Block]:
        """Returns the block corresponding to given block Id"""
        return self.blockchain.get_block_from_hash(blkId)
    
    def hash_timeout(self, blkId: str) -> Optional[Block]:
        self.receivedHashes[blkId].senders.popleft()
        if len(self.receivedHashes[blkId].senders) == 0:
            self.receivedHashes[blkId].timeout_active = False
            return None

        return self.receivedHashes[blkId].senders[0]

    def get_all_senders(self, blkId: str) -> List[int]:
        return self.receivedHashes[blkId].all_senders

    def add_block(self, block: Block, arrTime : float) -> bool:
        """
        Adds a new block to the blockchain, check for change in longest chain and updates the mempool.

        Args:
            block (Block): The new block to add.
            arrTime (float): The time the block was received.

        Returns:
            bool: True if the longest chain changed, False otherwise.
        """
        self.receivedHashes.pop(block.blkId, None)

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

    def set_miningBlk(self, blkId: str):
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
        txns.append(Transaction(-1, self.peerId, Block.miningReward)) # Coinbase

        for txn in self.mempool:
            if currentBalance[txn.senID] < peerSpent[txn.senID] + txn.amt:
                continue
            peerSpent[txn.senID] += txn.amt
            txns.append(txn)
            if len(txns) == 1000:
                break
        return txns


    def log_tree(self, folder: str):
        """Logs the blockchain tree to a file."""
        self.blockchain.print_tree(filename=f"{folder}/Peer_{self.peerId}.csv")