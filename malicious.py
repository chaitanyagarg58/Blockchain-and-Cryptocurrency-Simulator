from enum import Enum, auto
from block import Block
from transaction import Transaction
from blockchainTree import BlockchainTree
from collections import defaultdict
import random
from typing import List
from peer import PeerNode, CPUType, NetworkType


class MaliciousNode(PeerNode):

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