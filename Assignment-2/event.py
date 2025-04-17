from enum import Enum, auto
from block import Block
from transaction import Transaction
from typing import Optional

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
    def __init__(self, etype: EventType, channel: int, timestamp: int, senderPeerId: int, peerId: int, timeoutTargetId: Optional[int] = None, blkId: Optional[str] = None, block: Optional[Block] = None, transaction: Optional[Transaction] = None):
        """
        Event representing a specific action in the simulation (block or transaction related).
        
        Args:
            etype (EventType): Type of the event.
            channel (int): Channel of Network over which Event is sent. (in case of Propagate event)
            timestamp (int): The time at which the event occurs.
            senderPeerId (int): ID of the peer that sent the event. (in case of Propagate event)
            peerId (int): ID of the peer the event is being sent to.
            timeoutTargetId (Optional[int]): peerId which timed out on get request (if applicable).
            blkId (Optional[str]): Hash of block associated with the event (if applicable).
            block (Optional[Block]): Block associated with the event (if applicable).
            transaction (Optional[Transaction]): Transaction associated with the event (if applicable).
        """

        self.etype = etype
        self.channel = channel
        self.timestamp = timestamp
        self.senderPeerId = senderPeerId
        self.peerId = peerId
        self.timeoutTargetId = timeoutTargetId
        self.blkId = blkId
        self.block = block
        self.transaction = transaction