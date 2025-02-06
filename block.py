from transaction import Transaction
from typing import List, Dict

class Block:
    miningReward = 50
    BlkCounter = 0
    peerIds = []

    def __init__(self, creatorId: int, txns: List['Transaction'], parentBlockId: int, parentBlockBalance: Dict[int, int], depth: int, cpu: int, net: int):
        """
        Args:
            creatorId (int): Miner ID.
            txns (List[Transaction]): Transactions in a block
            parentBlockId (int): ID of parent block
            parentBlockBalance (Dict[int, int]): Balance snapshot before this block
            depth (int): Block depth in the chain
        """
        
        # Unique Block Id is set using a static counter variable
        self.BlkID = Block.BlkCounter
        Block.BlkCounter += 1

        self.creatorID = creatorId
        self.Txns = set(txns)
        self.size = (len(txns) + 1) * 8         # In Kilobits, including coinbase
        self.parentBlkID = parentBlockId
        self.depth = depth
        self.cpu = cpu
        self.net = net

        ## Balance snapshot after this block (assuming block is valid)
        self.peerBalance = {peerId: 0 for peerId in Block.peerIds}
        if parentBlockBalance != None:
            self.peerBalance = dict(parentBlockBalance)
            
            # coinbase
            self.peerBalance[self.creatorID] += Block.miningReward

            for txn in self.Txns:
                self.peerBalance[txn.senID] -= txn.amt
                self.peerBalance[txn.recID] += txn.amt
            
            
