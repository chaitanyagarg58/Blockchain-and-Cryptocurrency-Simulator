from transaction import Transaction
from typing import List, Dict
from hashlib import sha256

class Block:
    miningReward = 50
    hashSize = 0.512      # In Kilobits
    peerIds = []

    def __init__(self, creatorId: int, txns: List['Transaction'], parentBlockId: str, parentBlockBalance: Dict[int, int], depth: int, timestamp: float):
        """
        Args:
            creatorId (int): Miner ID.
            txns (List[Transaction]): Transactions in a block
            parentBlockId (str): ID of parent block
            parentBlockBalance (Dict[int, int]): Balance snapshot before this block
            depth (int): Block depth in the chain
            timestamp (float): Timestamp included by miner in block (The time when miner starting mining, not when it was mined).
        """
        self.creatorID = creatorId
        self.Txns = txns
        self.size = len(txns) * 8         # In Kilobits, including coinbase
        self.parentBlkID = parentBlockId
        self.depth = depth
        self.timestamp = timestamp

        ## Balance snapshot after this block (assuming block is valid)
        self.peerBalance = {peerId: 0 for peerId in Block.peerIds}
        if parentBlockBalance != None:
            self.peerBalance = dict(parentBlockBalance)

            for txn in self.Txns:
                if txn.senID != -1:
                    self.peerBalance[txn.senID] -= txn.amt
                self.peerBalance[txn.recID] += txn.amt

        # Unique Block Id is set using proper hashing
        self.blkId = sha256(str(self).encode()).hexdigest()

    def get_merkle_root(self) -> str:
        """Returns the Merkle Root of the Transactions in block"""
        if len(self.Txns) == 0:
            return ""
        txns_hash = [sha256(str(txn).encode()).hexdigest() for txn in self.Txns]

        while len(txns_hash) > 1:
            if len(txns_hash) % 2 != 0:
                txns_hash.append(sha256("".encode()).hexdigest())
            txns_hash = [sha256((txns_hash[i] + txns_hash[i+1]).encode()).hexdigest() for i in range(0, len(txns_hash), 2)]

        return txns_hash[0]

    def __str__(self):
        blockString = f"{self.parentBlkID}|{self.timestamp}|{self.get_merkle_root()}|"
        for txn in self.Txns:
            blockString += f"|{str(txn)}"
        return blockString
