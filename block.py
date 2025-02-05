from transaction import Transaction
from typing import List

class Block:
    MINING_REWARD = 50
    BlkCounter = 0
    peerIds = []

    def __init__(self, creatorId: int, txns: List['Transaction'], parentBlockId: int, parentBlockBalance: dict, depth: int):
        self.BlkID = Block.BlkCounter
        Block.BlkCounter += 1
        self.creatorID = creatorId
        self.Txns = set(txns) ## Set of Transactions in this block
        self.size = (len(txns) + 1) * 8 ## In Kilobits, including coinbase
        self.parentBlkID = parentBlockId
        self.depth = depth

        ### peerBalance is what the balance would be after this block.
        self.peerBalance = {peerId: 0 for peerId in Block.peerIds}
        if parentBlockBalance != None:
            self.peerBalance = dict(parentBlockBalance)
            
            # coinbase
            self.peerBalance[self.creatorID] += 50

            for txn in self.Txns:
                self.peerBalance[txn.senID] -= txn.amt
                self.peerBalance[txn.recID] += txn.amt
            
            
