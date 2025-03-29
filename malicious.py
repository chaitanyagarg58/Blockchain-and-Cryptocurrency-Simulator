from block import Block
from maliciousBlockchainTree import MaliciousBlockchainTree
from config import Config
from typing import List, Tuple, Optional
from peer import PeerNode, CPUType, NetworkType


class MaliciousNode(PeerNode):
    RingmasterId = None

    def __init__(self, peerId: int, netType: NetworkType, cpuType: CPUType, hashingPower: float, genesisBlock: Block):
        """
        Initializes a MaliciousNode.

        Args:
            peerId (int): Unique identifier for the peer.
            netType (NetworkType): Network speed type.
            cpuType (CPUType): CPU performance type.
            hashingPower (float): Mining power of the peer.
            genesisBlock (Block): The initial block of the blockchain.
        """
        super().__init__(peerId, netType, cpuType, hashingPower, genesisBlock)

        self.blockchain = MaliciousBlockchainTree(genesisBlock)
        self.overlay_connectedPeers = []
        self.overlay_pij = {}
        self.overlay_cij = {}

    def add_overlay_connected_peer(self, connectedPeerId: int):
        """Add a overlay connected peer."""
        self.overlay_connectedPeers.append(connectedPeerId)

    def add_overlay_propogation_link_delay(self, connectedPeerId: int, pij : float):
        """Sets the propagation delay for a overlay connection to a peer."""
        self.overlay_pij[connectedPeerId] = pij

    def add_overlay_link_speed(self, connectedPeerId : int, cij : float):
        """Sets the link speed for a overlay connection to a peer."""
        self.overlay_cij[connectedPeerId] = cij

    def get_connected_list(self, creatorId: int) -> List[Tuple[int, int]]:
        """Get list of connections where we want to forward block hash, based on creator id."""
        forwarding_list = self.get_overlay_connections()
        if creatorId != MaliciousNode.RingmasterId:
            forwarding_list += self.get_public_connections()
        return forwarding_list
    
    def get_overlay_connections(self) -> List[Tuple[int, int]]:
        """Get all overlay connections."""
        return [(overlay_connectedPeerId, 2) for overlay_connectedPeerId in self.overlay_connectedPeers]
    
    def get_public_connections(self) ->List[Tuple[int, int]]:
        """Get all public connections."""
        return super().get_connected_list(-1)

    def get_channel_details(self, connectedPeerId: int, channel: int) -> Tuple[int, int]:
        """Get channel details."""
        if channel == 1:
            return self.pij[connectedPeerId], self.cij[connectedPeerId]
        else:
            return self.overlay_pij[connectedPeerId], self.overlay_cij[connectedPeerId]

    def get_block_for_get_request(self, channel: int, blkId: str) -> Optional[Block]:
        """Returns the block corresponding to given block Id (used only when needing to forward block due to get request).
        May with-hold block based on block creator and channel which asked for block."""
        block = self.blockchain.get_block_from_hash(blkId)
        if Config.remove_eclipse or block.creatorID == MaliciousNode.RingmasterId or channel != 1:
            return block
        return None
    
    def broadcast_seen(self, blkId: str) -> bool:
        """Checks if broadcast event was seen."""
        return self.blockchain.check_broadcast(blkId)

    def get_private_chain(self, blkId: str) -> List[str]:
        """Get Private chain ending with given block id. Also adds them to public chain."""
        private_chain = self.blockchain.get_private_chain(blkId)
        ret = []
        for private_block, arrTime in private_chain:
            super().add_block(private_block, arrTime)
            ret.append(private_block.blkId)
        return ret

    def add_block(self, block: Block, arrTime : float) -> Optional[str]:
        """
        Adds a new block to the blockchain (private or public).
        Returns:
            Optional[str]: None
        """
        if block.creatorID != MaliciousNode.RingmasterId:
            super().add_block(block, arrTime)
            return None
        
        self.receivedHashes.pop(block.blkId, None)
        self.blockchain.add_selfish_block(block, arrTime)

class RingMasterNode(MaliciousNode):

    def __init__(self, peerId: int, netType: NetworkType, cpuType: CPUType, hashingPower: float, genesisBlock: Block):
        """
        Initializes a RingMaster.

        Args:
            peerId (int): Unique identifier for the peer.
            netType (NetworkType): Network speed type.
            cpuType (CPUType): CPU performance type.
            hashingPower (float): Mining power of the peer.
            genesisBlock (Block): The initial block of the blockchain.
        """
        super().__init__(peerId, netType, cpuType, hashingPower, genesisBlock)

    def get_lastBlk(self) -> Block:
        """Returns the last block in the longest chain."""
        honest = self.blockchain.get_lastBlock()
        private = self.blockchain.get_last_private_block()
        if private is None or private.depth < honest.depth:
            return honest
        else:
            return private

    def add_block(self, block: Block, arrTime : float) -> Optional[str]:
        """
        Adds a new block to the blockchain (private or public).
        Implements Selfish Mining.
        Returns:
            Optional[str]: None
        """
        if block.creatorID == MaliciousNode.RingmasterId:
            super().add_block(block, arrTime)
            return None
        

        super().add_block(block, arrTime)
        honest_block = self.blockchain.get_lastBlock()
        private_block = self.blockchain.get_last_private_block()
        if private_block is None or private_block.depth > honest_block.depth + 1:
            return None
        
        return private_block.blkId
        
    def get_last_private_block(self) -> Optional[Block]:
        """Get last private block."""
        return self.blockchain.get_last_private_block()