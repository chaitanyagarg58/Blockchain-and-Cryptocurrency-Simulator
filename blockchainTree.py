from block import Block
from collections import defaultdict

class BlockchainTree:
    def __init__(self, genesisBlock: Block):
        self.blocks = {genesisBlock.BlkID: genesisBlock}
        self.children = defaultdict(list)
        self.genesisBlock = genesisBlock
        self.longestChainTip = genesisBlock.BlkID

        self.unverifiedBlocks = []
    
    def add_block(self, block: Block):
        if block.parentBlkID not in self.blocks:
            self.unverifiedBlocks.append(block)
            return True
        
        if not self.verify_correctness(block):
            return False

        self.blocks[block.BlkID] = block
        self.children[block.parentBlkID].append(block.BlkID)

        ### TODO add code for branch switching
        if self.longestChainTip == block.parentBlkID: ## current longest chain extended
            self.longestChainTip = block.BlkID

        elif self.blocks[self.longestChainTip].depth < block.depth: ## new block on some other branch and that is now the longest chain
            self.longestChainTip = block.BlkID



    def verify_correctness(self, block: Block): # May be better to have it in PeerNode
        pass
