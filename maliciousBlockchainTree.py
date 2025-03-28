from block import Block
from blockchainTree import BlockchainTree
from typing import List, Tuple, Optional


class MaliciousBlockchainTree(BlockchainTree):
    def __init__(self, genesisBlock: Block):
        """
        Initializes the blockchain tree with the genesis block

        Args:
            genesisBlock (Block): The genesis Block.
        """
        super().__init__(genesisBlock)

        self.privateChain: List[Tuple[Block, float]] = []

        self.seenBroadcasts = set()

    def add_selfish_block(self, block: Block, arrTime: float):
        self.privateChain.append((block, arrTime))
        self.privateChain.sort(key=lambda x: x[0].depth)

    def check_broadcast(self, blkId: str) -> bool:
        return blkId in self.seenBroadcasts
    
    def check_block(self, blkId: str) -> bool:
        return super().check_block(blkId) or (blkId in map(lambda x: x[0].blkId, self.privateChain))
    
    def get_block_from_hash(self, blkId: str) -> Block:
        block = next((block for block, _ in self.privateChain if block.blkId == blkId), None)
        if block is None:
            block = super().get_block_from_hash(blkId)

        assert block is not None, "Got get request for block, but don't have block"
        return block

    def get_last_private_block(self) -> Optional[Block]:
        if len(self.privateChain) == 0:
            return None
        return self.privateChain[-1][0]

    def get_private_chain(self, blkId: str) -> List[Tuple[Block, float]]:
        self.seenBroadcasts.add(blkId)

        ret = []
        idx = -1
        for idx, (privateblock, arrTime) in enumerate(self.privateChain):
            ret.append((privateblock, arrTime))
            if privateblock.blkId == blkId:
                break
        self.privateChain = self.privateChain[idx + 1:]
        return ret