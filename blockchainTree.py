from block import Block
from collections import defaultdict


class BlockchainTree:

    def __init__(self, genesisBlock: Block):
        self.seenBlocks = {genesisBlock.BlkID: genesisBlock}
        self.children = defaultdict(list)
        self.longestChainTip = genesisBlock.BlkID
        self.prevChainTip = -1
        self.danglingBlocksList = defaultdict(list)
        self.VerifiedBlocks = [genesisBlock.BlkID]
        self.arrTime = {genesisBlock.BlkID : 0}


    def check_block(self, blockId: int):
        return blockId in self.seenBlocks
    

    def lca(self, blk1 = - 1, blk2 = -1):
        if blk1 == -1:
            blk1 = self.longestChainTip
        if blk2 == -1:
            blk2 = self.prevChainTip
        
        if self.prevChainTip == -1:
            return 0
        
        block1 = self.seenBlocks[blk1]
        block2 = self.seenBlocks[blk2]
        
        while block1.depth < block2.depth:
            block2 = self.seenBlocks[block2.parentBlkID]
        while block1.depth > block2.depth:
            block1 = self.seenBlocks[block1.parentBlkID]
        while block1.BlkID != block2.BlkID:
            block2 = self.seenBlocks[block2.parentBlkID]
            block1 = self.seenBlocks[block1.parentBlkID]
        return block1.BlkID
    

    def add_dangling_block(self, block: Block):
        if not self.verify_correctness(block):
            self.recursive_deletion(block.BlkID)
            return False

        ## Add blockId in self.VerifiedBlocks
        self.VerifiedBlocks.append(block.BlkID)

        # Add Node to BlockChainTree
        self.children[block.parentBlkID].append(block.BlkID)

        ### TODO add code for branch switching->Done
        if self.longestChainTip == block.parentBlkID: ## current longest chain extended
            self.longestChainTip = block.BlkID
        elif self.seenBlocks[self.longestChainTip].depth < block.depth: ## new block on some other branch and that is now the longest chain
            self.longestChainTip = block.BlkID

        ## Recursive addition of Dangling Blocks
        if block.parentBlkID in self.danglingBlocksList:
            for child in self.danglingBlocksList[block.parentBlkID]:
                self.add_dangling_block(self.seenBlocks[child])
            del self.danglingBlocksList[block.parentBlkID]


    def add_block(self, block: Block, arrTime: float):
        ## if block seen, return else continue
        if self.check_block(block.BlkID):
            return False
        
        self.arrTime[block.BlkID] = arrTime
        self.seenBlocks[block.BlkID] = block
        ## if block parent not seen, add block to dangling blocks and return
        if block.parentBlkID not in self.VerifiedBlocks:
            self.danglingBlocksList[block.parentBlkID].append(block.BlkID)
            return True
        
        ## if block not verified, recursive deletion of subtree rooted 
        if not self.verify_correctness(block):
            self.recursive_deletion(block.BlkID)
            return False

        ## Add blockId in self.VerifiedBlocks
        self.VerifiedBlocks.append(block.BlkID)

        # Add Node to BlockChainTree
        self.children[block.parentBlkID].append(block.BlkID)

        ### TODO add code for branch switching->Done
        if self.longestChainTip == block.parentBlkID: ## current longest chain extended
            self.prevChainTip = block.parentBlkID
            self.longestChainTip = block.BlkID
        elif self.seenBlocks[self.longestChainTip].depth < block.depth: ## new block on some other branch and that is now the longest chain
            self.prevChainTip = self.longestChainTip
            self.longestChainTip = block.BlkID
        else:
            self.prevChainTip = self.longestChainTip

        ## Recursive addition of Dangling Blocks
        if block.parentBlkID in self.danglingBlocksList:
            for child in self.danglingBlocksList[block.parentBlkID]:
                self.add_dangling_block(self.seenBlocks[child])
            del self.danglingBlocksList[block.parentBlkID]
            

    def recursive_deletion(self, blockId: int):
        if blockId in self.danglingBlocksList:
            for child in self.danglingBlocksList[blockId]:
                self.recursive_deletion(child)
            del self.danglingBlocksList[blockId]
        # self.seenBlocks[blockId] = None


    ## Checks the correctness of the block, uses parent block information
    def verify_correctness(self, block: Block): # May be better to have it in PeerNode
        parent =  self.seenBlocks[block.parentBlkID]
        cur_amt = {}
        for txn in parent.Txns:
            if txn.senID not in cur_amt:
                cur_amt[txn.senID] = 0
            cur_amt[txn.senID] += txn.amt
        for sen in cur_amt:
            if cur_amt[sen] > parent.peerBalance[sen]:
                return False
        return True
    
    
    def get_txn_set(self, blkId:int, lcaId:int):
        txnSet = set()
        block = self.seenBlocks[blkId]
        while block.BlkID != lcaId:
            txnSet = txnSet | block.Txns
            block = self.seenBlocks[block.parentBlkID]
        return txnSet
    

    def get_lastBlock(self):
        return self.seenBlocks[self.longestChainTip]


    ## File printing function
    def print_tree(self, filename = None):
        sortedIDs = sorted(self.arrTime, key = self.arrTime.get)
        if filename is None:
            filename = "graphData.txt"
        with open(filename, "w") as file:
            file.write(f"BlockId, ParentId, Arrival Time\n")
            for blockId in sortedIDs:
                file.write(f"{blockId}, {self.seenBlocks[blockId].parentBlkID}, {self.arrTime[blockId]:.2f}\n")
        