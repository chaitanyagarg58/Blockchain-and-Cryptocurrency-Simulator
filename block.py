from transaction import Transaction


class Block:
    MINING_REWARD = 50
    BlkCounter = 0

    def __init__(self, creatorId: int, size: int, parentBlockId: int, depth: int):
        self.BlkID = Block.BlkCounter
        Block.BlkCounter += 1
        self.creatorID = creatorId
        self.size = size
        self.Txns = None ## Set of Transactions in this block
        self.parentBlkID = parentBlockId
        self.depth = depth
