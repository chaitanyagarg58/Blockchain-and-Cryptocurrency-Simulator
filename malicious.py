from enum import Enum, auto
from block import Block
from transaction import Transaction
from blockchainTree import BlockchainTree
from collections import defaultdict
import random
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

        self.overlay_connectedPeers = []
        self.overlay_pij = {}
        self.overlay_cij = {}

    def add_overlay_connected_peer(self, connectedPeerId: int):
        self.overlay_connectedPeers.append(connectedPeerId)

    def add_overlay_propogation_link_delay(self, connectedPeerId: int, pij : float):
        self.overlay_pij[connectedPeerId] = pij

    def add_overlay_link_speed(self, connectedPeerId : int, cij : float):
        self.overlay_cij[connectedPeerId] = cij

    def get_connected_list(self, creatorId: int) -> List[Tuple[int, int]]:
        forwarding_list = [(overlay_connectedPeerId, 2) for overlay_connectedPeerId in self.overlay_connectedPeers]
        if creatorId != MaliciousNode.RingmasterId:
            forwarding_list += [(connectedPeerId, 1) for connectedPeerId in self.connectedPeers]
        return forwarding_list
    
    def get_channel_details(self, connectedPeerId: int, channel: int) -> Tuple[int, int]:
        if channel == 1:
            return self.pij[connectedPeerId], self.cij[connectedPeerId]
        else:
            return self.overlay_pij[connectedPeerId], self.overlay_cij[connectedPeerId]

    def get_block_for_get_request(self, channel: int, blkId: str) -> Optional[Block]:
            if channel == 1:
                return None
            return self.blockchain.get_block_from_hash(blkId)

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