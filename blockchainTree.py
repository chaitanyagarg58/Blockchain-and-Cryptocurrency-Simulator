from block import Block
from collections import defaultdict

class BlockchainTree:
    def __init__(self, genesisBlock: Block):
        self.genesisBlock = genesisBlock #= {genesisBlock.BlkID: genesisBlock}
        self.children = defaultdict(list)
        self.genesisBlock = genesisBlock
        self.longestChainTip = genesisBlock.BlkID
        self.danglingBlocksList = defaultdict(list)
        self.VerifiedBlocks = [0]
        self.danglingBlocks = []

    def check_block(self, blockId: int):
        if blockId in self.VerifiedBlocks:
            return True
        elif blockId in self.danglingBlocks:
            return True
        else:
            return False
    
    def add_block(self, block: Block, isDanglingAddition = False):

        if self.check_block(block.BlkID) and not isDanglingAddition:
            return False
        
        if block.parentBlkID not in self.VerifiedBlocks:
            self.danglingBlocksList[block.parentBlkID].append(block)
            return True
        
        if not self.verify_correctness(block):
            self.recursive_deletion(block.BlkID)
            return False

        ## TODO : Add blockId in self.VerifiedBlocks and remove from self.danglingBlocks

        # self.blocks[block.BlkID] = block
        self.children[block.parentBlkID].append(block.BlkID)

        ### TODO add code for branch switching
        if self.longestChainTip == block.parentBlkID: ## current longest chain extended
            self.longestChainTip = block.BlkID

        elif self.blocks[self.longestChainTip].depth < block.depth: ## new block on some other branch and that is now the longest chain
            self.longestChainTip = block.BlkID

        if block.parentBlkID in self.danglingBlocksList:
            for child in self.danglingBlocksList[block.parentBlkID]:
                self.add_block(child, True)
            
            


    def verify_correctness(self, block: Block): # May be better to have it in PeerNode
        pass
