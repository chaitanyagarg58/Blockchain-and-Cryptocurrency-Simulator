from enum import Enum, auto
from block import Block
from transaction import Transaction
from blockchainTree import BlockchainTree
from dataclasses import dataclass, field
from config import Config
from typing import List, Dict, Set, Tuple, Optional


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
    """Metadata for tracking block hash propagation and handling."""
    all_senders: List[Tuple[int, int]] = field(default_factory=list) # list of all senders (including those who timedout)
    passive_senders: List[Tuple[int, int]] = field(default_factory=list)  # Peers who sent hash and not yet sent get request
    active_senders: List[Tuple[int, int]] = field(default_factory=list) # Peers who had been sent get request and timeout is active (in sequence). len is maximum 1 when no counter measure

class PeerNode:
    """Represents a Honest Peer/Miner in the blockchain P2P network."""

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

        ## Counter Measure for eclipse attack
        self.peerPendingRequests: Dict[int, Set[str]] = {}  # For each connected peer, the set of blkIds for which get request is sent, but block not received

    def add_connected_peer(self, connectedPeerId: int):
        """Add a connected peer."""
        self.connectedPeers.append(connectedPeerId)
        self.peerPendingRequests[connectedPeerId] = set()

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

    def respond_to_get_received(self, blkId: str, senderId: int, channel: int):
        """Handles the response when a requested block is received."""
        if channel == 1:
            self.peerPendingRequests[senderId].discard(blkId)

    def trust_on_peer(self, questionedPeerId: int, channel: int) -> bool:
        """Used only when Counter Measure is enabled. Checks if given connection can be trusted to respond to get request."""
        if channel == 2:
            return True
        trust_active_peer = True
        for pending_blkId in self.peerPendingRequests[questionedPeerId]:
            if pending_blkId in self.receivedHashes and (questionedPeerId, channel) in self.receivedHashes[pending_blkId].active_senders:
                continue # excuse this block
            else:
                # Don't trust this peer
                trust_active_peer = False
                break
        return trust_active_peer

    def add_hash(self, blkId: str, senderId: int, channel: int) -> bool:
        """
        Adds a block hash to the received Hashes.
        Returns:
            bool: True if a new get request should be created for this sender right now, False otherwise.
        """
        if blkId not in self.receivedHashes:
            self.receivedHashes[blkId] = BlockHashMetadata()

        self.receivedHashes[blkId].passive_senders.append((senderId, channel))
        self.receivedHashes[blkId].all_senders.append((senderId, channel))

        if Config.counter_measure:
            for active_peer, active_channel in self.receivedHashes[blkId].active_senders:
                if self.trust_on_peer(active_peer, active_channel):
                    return False
            return True

        return len(self.receivedHashes[blkId].active_senders) == 0
    
    def scheduled_get(self, peerId: int, channel: int, blkId: str):
        """Updates meta data to indicate that a get request has been scheduled corresponding to given connection and block id."""
        self.receivedHashes[blkId].passive_senders.remove((peerId, channel))
        self.receivedHashes[blkId].active_senders.append((peerId, channel))

        if channel == 1:
            self.peerPendingRequests[peerId].add(blkId)

    def get_block_for_get_request(self, channel: int, blkId: str) -> Optional[Block]:
        """Returns the block corresponding to given block Id (used only when needing to forward block due to get request)."""
        return self.blockchain.get_block_from_hash(blkId)

    def hash_timeout(self, targetId: int, channel: int, blkId: str) -> Optional[Tuple[int, int]]:
        """Process Timeout event and return which connection new get request should be scheduled to."""
        self.receivedHashes[blkId].active_senders.remove((targetId, channel))

        if Config.counter_measure:
            for active_peer, active_channel in self.receivedHashes[blkId].active_senders:
                if self.trust_on_peer(active_peer, active_channel):
                    return None

            for passive_peer, passive_channel in self.receivedHashes[blkId].passive_senders:
                if self.trust_on_peer(passive_peer, passive_channel):
                    return passive_peer, passive_channel

        if len(self.receivedHashes[blkId].active_senders) != 0:
            return None

        if len(self.receivedHashes[blkId].passive_senders) == 0:
            return None
        return self.receivedHashes[blkId].passive_senders[0]

    def get_all_senders(self, blkId: str) -> List[Tuple[int, int]]:
        """Return all peers who sent given hash."""
        return map(lambda x: x[0], self.receivedHashes[blkId].all_senders)
    
    def get_connected_list(self, creatorId: int) -> List[Tuple[int, int]]:
        """Get all connected peers."""
        return [(connectedPeerId, 1) for connectedPeerId in self.connectedPeers]
    
    def get_channel_details(self, connectedPeerId: int, channel: int) -> Tuple[int, int]:
        """Get channel details."""
        return self.pij[connectedPeerId], self.cij[connectedPeerId]

    def add_block(self, block: Block, arrTime : float) -> Optional[str]:
        """
        Adds a new block to the blockchain, check for change in longest chain and updates the mempool.
        Returns:
            Optional[str]: None.
        """
        self.receivedHashes.pop(block.blkId, None)

        self.blockchain.add_block(block, arrTime)
        
        # Update mempool for the longest chain
        lca = self.blockchain.lca()
        insert_set = self.blockchain.get_txn_set(self.blockchain.prevChainTip, lca)
        del_set = self.blockchain.get_txn_set(self.blockchain.longestChainTip, lca)
        self.mempool = self.mempool | insert_set
        self.mempool = self.mempool.difference(del_set)

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
        return self.miningBlkId != self.get_lastBlk().blkId

    def get_lastBlk(self) -> Block:
        """Returns the last block in the longest chain."""
        return self.blockchain.get_lastBlock()
    
    def sample_transactions(self) -> List['Transaction']:
        """
        Selects valid transactions from the mempool based on account balances.
        Returns:
            List[Transaction]: A list of transactions that can be included in a new block.
        """

        currentBalance = self.get_lastBlk().peerBalance
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