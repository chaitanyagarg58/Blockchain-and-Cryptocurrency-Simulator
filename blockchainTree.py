from transaction import Transaction
from block import Block
from collections import defaultdict
from typing import Set

class BlockchainTree:
    def __init__(self, genesisBlock: Block):
        """
        Initializes the blockchain tree with the genesis block

        Args:
            genesisBlock (Block): The genesis Block.
        """
        self.seenBlocks = {genesisBlock.BlkID: genesisBlock}
        self.children = defaultdict(list)
        self.longestChainTip = genesisBlock.BlkID
        self.prevChainTip = "-1"
        self.danglingBlocksList = defaultdict(list)
        self.VerifiedBlocks = [genesisBlock.BlkID]
        self.arrTime = {genesisBlock.BlkID : 0}


    def check_block(self, blockId: str) -> bool:
        """
        Checks if the block has been received before. (Mainly for loop less forwarding).

        Returns:
            bool: True if the block is seen/received before, False otherwise.
        """
        return blockId in self.seenBlocks
    

    def lca(self, blk1: str = "-1", blk2: str = "-1") -> str:
        """
        Finds the Least Common Ancestor (LCA) of the two blocks in the blockchain.

        Args:
            blk1 (str): The ID of the first block (default is the longest chain tip).
            blk2 (str): The ID of the second block (default is the previous chain tip).
        
        Returns:
            str: The ID of the lowest common ancestor block.
        """
        if blk1 == "-1":
            blk1 = self.longestChainTip
        if blk2 == "-1":
            blk2 = self.prevChainTip
        
        if self.prevChainTip == "-1":
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
        """
        Verifies the correctness of the dangling block and Adds it to the blockchain. (recursively)

        Args:
            block (Block): The dangling block to add.
        """
        if not self.verify_correctness(block):
            self.recursive_deletion(block.BlkID)
            return

        ## Add blockId in self.VerifiedBlocks
        self.VerifiedBlocks.append(block.BlkID)

        ## Add Node to BlockChainTree
        self.children[block.parentBlkID].append(block.BlkID)

        ## Switch Longest Chain if applicable
        if self.seenBlocks[self.longestChainTip].depth < block.depth:
            self.longestChainTip = block.BlkID

        ## Recursive addition of Dangling Blocks
        if block.BlkID in self.danglingBlocksList:
            for childId in self.danglingBlocksList[block.BlkID]:
                self.add_dangling_block(self.seenBlocks[childId])
            del self.danglingBlocksList[block.BlkID]


    def add_block(self, block: Block, arrTime: float):
        """
        Adds a new block to the blockchain tree.

        Args:
            block (Block): The block to add.
            arrTime (float): The arrival time of the block.
        """
        # if block seen, return else continue
        if self.check_block(block.BlkID):
            return
        
        self.arrTime[block.BlkID] = arrTime
        self.seenBlocks[block.BlkID] = block
        ## if block parent not seen, add block to dangling blocks and return
        if block.parentBlkID not in self.VerifiedBlocks:
            self.danglingBlocksList[block.parentBlkID].append(block.BlkID)
            return
        
        ## if block not verified, recursive deletion of subtree rooted 
        if not self.verify_correctness(block):
            self.recursive_deletion(block.BlkID)
            return

        ## Add blockId in self.VerifiedBlocks
        self.VerifiedBlocks.append(block.BlkID)

        # Add Node to BlockChainTree
        self.children[block.parentBlkID].append(block.BlkID)

        ### TODO add code for branch switching->Done
        self.prevChainTip = self.longestChainTip
        if self.seenBlocks[self.longestChainTip].depth < block.depth:
            self.longestChainTip = block.BlkID

        ## Recursive addition of Dangling Blocks
        if block.BlkID in self.danglingBlocksList:
            for childId in self.danglingBlocksList[block.BlkID]:
                self.add_dangling_block(self.seenBlocks[childId])
            del self.danglingBlocksList[block.BlkID]
            

    def recursive_deletion(self, blockId: str):
        """
        Recursively deletes dangling blocks (due to parent being invalid).

        Args:
            blockId (int): The ID of the parent block, whose dangling children are to be deleted
        """
        if blockId in self.danglingBlocksList:
            for childId in self.danglingBlocksList[blockId]:
                self.recursive_deletion(childId)
            del self.danglingBlocksList[blockId]


    def verify_correctness(self, block: Block) -> bool:
        """
        Verifies the correctness of a block based on its parent block.

        Args:
            block (Block): The block to verify.
        
        Returns:
            bool: True if the block is correct, otherwise False.
        """
        parent =  self.seenBlocks[block.parentBlkID]
        cur_amt = {}

        if block.Txns[0].senID != -1 or block.Txns[0].amt != Block.miningReward:
            return False

        for txn in block.Txns[1:]:
            if txn.senID not in cur_amt:
                cur_amt[txn.senID] = 0
            cur_amt[txn.senID] += txn.amt

        for sen in cur_amt:
            if cur_amt[sen] > parent.peerBalance[sen]:
                return False
        return True
    
    
    def get_txn_set(self, blkId: str, ancestorId: str) -> Set['Transaction']:
        """
        Gets the set of transactions from the block (inclusive) to its ancestor (exclusive).

        Args:
            blkId (str): The ID of the block.
            ancestorId (str): The ID of ancestor.
        
        Returns:
            Set[Transaction]: The set of transactions.
        """
        txnSet = set()
        block = self.seenBlocks[blkId]
        while block.BlkID != ancestorId:
            txnSet = txnSet | set(block.Txns[1:])
            block = self.seenBlocks[block.parentBlkID]
        return txnSet
    

    def get_lastBlock(self) -> Block:
        """Gets the last block in the longest chain."""
        return self.seenBlocks[self.longestChainTip]


    def print_tree(self, filename: str):
        """Prints the blockchain tree to a file."""

        sortedIDs = sorted(self.arrTime, key = self.arrTime.get)

        with open(filename, "w") as file:
            file.write(f"BlockId, ParentId, creatorId, Arrival Time, Depth, Block-Size\n")
            for blockId in sortedIDs:
                if blockId in self.VerifiedBlocks:
                    file.write(f"{blockId}, {self.seenBlocks[blockId].parentBlkID}, {self.seenBlocks[blockId].creatorID}, {self.arrTime[blockId]:.2f}, {self.seenBlocks[blockId].depth}, {self.seenBlocks[blockId].size}\n")
