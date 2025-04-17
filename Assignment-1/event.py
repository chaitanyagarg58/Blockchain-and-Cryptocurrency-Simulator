from enum import Enum, auto
from block import Block
from transaction import Transaction

class EventType(Enum):
    # Types of events in the blockchain simulation
    BLOCK_GENERATE = auto()
    BLOCK_PROPAGATE = auto()
    TRANSACTION_GENERATE = auto()
    TRANSACTION_PROPAGATE = auto()


class Event:
    def __init__(self, etype: EventType, timestamp: int, senderPeerId: int, peerId: int, block: Block = None, transaction: Transaction = None):
        """
        Event representing a specific action in the simulation (block or transaction related).
        
        Args:
            etype (EventType): Type of the event.
            timestamp (int): The time at which the event occurs.
            senderPeerId (int): ID of the peer that sent the event. (int case of Propagate event)
            peerId (int): ID of the peer the event is being sent to.
            block (Block, optional): Block associated with the event (if applicable).
            transaction (Transaction, optional): Transaction associated with the event (if applicable).
        """

        self.etype = etype
        self.timestamp = timestamp
        self.senderPeerId = senderPeerId
        self.peerId = peerId
        self.block = block
        self.transaction = transaction