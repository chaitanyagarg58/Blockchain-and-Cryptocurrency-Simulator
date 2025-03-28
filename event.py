from enum import Enum, auto
from block import Block
from transaction import Transaction

class EventType(Enum):
    # Types of events in the blockchain simulation
    BLOCK_GENERATE = auto()

    HASH_PROPAGATE = auto()
    GET_REQUEST = auto()
    TIMEOUT_EVENT = auto()
    BLOCK_PROPAGATE = auto()
    BROADCAST_PRIVATECHAIN = auto()
    FINALIZE_EVENT = auto()

    TRANSACTION_GENERATE = auto()
    TRANSACTION_PROPAGATE = auto()


class Event:
    def __init__(self, etype: EventType, channel: int, timestamp: int, senderPeerId: int, peerId: int, blkId: str = None, block: Block = None, transaction: Transaction = None):
        """
        Event representing a specific action in the simulation (block or transaction related).
        
        Args:
            etype (EventType): Type of the event.
            channel (int): Channel of Network over which Event is sent. (int case of Propagate event)
            timestamp (int): The time at which the event occurs.
            senderPeerId (int): ID of the peer that sent the event. (in case of Propagate event)
            peerId (int): ID of the peer the event is being sent to.
            blkId (str, optional): Hash of block associated with the event (if applicable).
            block (Block, optional): Block associated with the event (if applicable).
            transaction (Transaction, optional): Transaction associated with the event (if applicable).
        """

        self.etype = etype
        self.channel = channel
        self.timestamp = timestamp
        self.senderPeerId = senderPeerId
        self.peerId = peerId
        self.blkId = blkId
        self.block = block
        self.transaction = transaction