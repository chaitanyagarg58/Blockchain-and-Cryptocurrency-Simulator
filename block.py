from transaction import *


class Block:
    def __init__(self, blockId, creatorId, size, prevBlockId):
        self.BlkID = blockId
        self.creatorID = creatorId
        self.size = size
        self.Txns = None ## Set of Transactions in this block
        self.prevBlkID = prevBlockId