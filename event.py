from enum import Enum, auto
from block import Block
from transaction import Transaction

class EventType(Enum):
    BLOCK_GENERATE = auto()
    BLOCK_PROPAGATE = auto()
    TRANSACTION_GENERATE = auto()
    TRANSACTION_PROPAGATE = auto()


class Event:
    def __init__(self, etype: EventType, timestamp: int, senderPeerId: int, peerId: int):
        self.etype = etype
        self.timestamp = timestamp
        self.senderPeerId = senderPeerId
        self.peerId = peerId
        self.block = None
        self.transaction = None


    def __lt__(self, other):
        return self.timestamp < other.timestamp