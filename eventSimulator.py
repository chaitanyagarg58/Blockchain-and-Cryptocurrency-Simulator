import simpy
from event import EventType, Event
from peer import NetworkType, CPUType, PeerNode
from transaction import Transaction
from block import Block
import random
from tqdm import tqdm
from typing import List


class EventSimulator:
    def __init__(self, env: simpy.Environment, peers: List['PeerNode'], block_interarrival_time: float, transaction_mean_time: float, sim_time: float):
        """Initialize the simulator environment"""
        self.env = env
        self.peers = peers
        self.block_interarrival_time = block_interarrival_time
        self.transaction_mean_time = transaction_mean_time

        self.eventHandler = {}
        self.eventHandler[EventType.BLOCK_GENERATE] = self.process_block_generation
        self.eventHandler[EventType.BLOCK_PROPAGATE] = self.process_block_propagation
        self.eventHandler[EventType.TRANSACTION_GENERATE] = self.process_transaction_generation
        self.eventHandler[EventType.TRANSACTION_PROPAGATE] = self.process_transaction_propagation

        for peer in peers:
            self.schedule_transaction_generation(peer.peerId)
            self.schedule_block_generation(peer.peerId)
        
        self.progress_bar = tqdm(total=sim_time, desc="Simulation Progress", position=0, leave=True)
        self.last_update = 0

    def process_event(self, event: Event):
        """Process event based on its type"""

        if self.last_update < self.env.now:
            self.progress_bar.update(self.env.now - self.last_update)
            self.last_update = self.env.now

        eventType = event.etype
        handler = self.eventHandler.get(event.etype, None)
        if handler:
            handler(event)
        else:
            print(f"Unkown Event Type {eventType}")


    def schedule_event(self, event: Event, delay: float):
        """Schedule the given event at the given delay"""
        yield self.env.timeout(delay)
        self.process_event(event)


    #############################################
    ## BLOCK Generation Starts
    def schedule_block_generation(self, peerId:int):
        """Schedules the generation of a new block for the given peerId."""
        delay = random.expovariate(lambd= self.peers[peerId].hashingPower / self.block_interarrival_time)

        lastBlock = self.peers[peerId].get_lastBlk()
    
        txnList = self.peers[peerId].sample_transactions()
        parentBlkId = lastBlock.BlkID
        parentBlkBalance = lastBlock.peerBalance
        depth = lastBlock.depth + 1

        block = Block(creatorId=peerId, txns=txnList, parentBlockId=parentBlkId, parentBlockBalance=parentBlkBalance, depth=depth)
        self.peers[peerId].set_miningBlk(parentBlkId)

        event = Event(EventType.BLOCK_GENERATE, self.env.now + delay, None, peerId, block=block)
        self.env.process(self.schedule_event(event, delay=delay))

    def process_block_generation(self, event: Event):
        """
        Process the block generation event.
        
        If the longest chain has changed since this event was scheduled, this event is terminated. (We would have starting working on another block)
        Adds the block to the blockchain and propagated to connected peers.
        """
        peerId = event.peerId
        block = event.block

        if self.peers[peerId].get_lastBlk().BlkID != block.parentBlkID:
            return

        self.peers[peerId].add_block(block, self.env.now)

        for connectedPeerId in self.peers[peerId].connectedPeers:
            self.schedule_block_propagation(peerId, connectedPeerId, block)

        self.schedule_block_generation(peerId)
    ## BLOCK Generation Ends
    ##############################################


    ###############################################
    ## BLOCK Propagation Starts
    def schedule_block_propagation(self, senderId: int, receiverId: int, block: Block):
        """Schedules the propagation of the block from sender to receiver."""
        pij = self.peers[senderId].pij[receiverId]
        cij = self.peers[senderId].cij[receiverId]
        dij = random.expovariate(lambd=cij/96)
        delay = pij + block.size / cij  + dij
        delay = delay / 1000 ## delay in seconds

        event = Event(EventType.BLOCK_PROPAGATE, self.env.now + delay, senderId, receiverId, block=block)
        self.env.process(self.schedule_event(event, delay=delay))


    def process_block_propagation(self, event: Event):
        """
        Processes the block propagation event.

        Checks if the block has been seen before for correct loopless forwarding implementation.
        Verifies and adds the block to the blockchain.
        If the longest chain is changed as a consequence of this block, we schedule block generation on the longest chain for this Peer.
        Propagate this event to connected peer. (Loopless forwarding)
        """
        peerId = event.peerId
        if self.peers[peerId].block_seen(event.block):
            return
        
        block = event.block

        self.peers[peerId].add_block(block, self.env.now)
        if self.peers[peerId].mining_check():
            self.schedule_block_generation(peerId)
        
        for connectedPeerId in self.peers[peerId].connectedPeers:
            if connectedPeerId == event.senderPeerId:
                continue
            self.schedule_block_propagation(peerId, connectedPeerId, block)
    ## BLOCK Propagation Ends
    ##############################################


    ###############################################
    ## Transaction Generation Starts
    def schedule_transaction_generation(self, peerId: int):
        """Schedules the generation of a new transaction for the given peerId."""
        delay = random.expovariate(lambd=1/self.transaction_mean_time)
        event = Event(EventType.TRANSACTION_GENERATE, self.env.now + delay, None, peerId)
        self.env.process(self.schedule_event(event, delay=delay))

    def process_transaction_generation(self, event: Event):
        """
        Process the transaction generation event.

        Creates a valid transaction, adds it to mempool, and propagates to connected peers.
        """
        peerId = event.peerId
        currentBalance = self.peers[peerId].get_lastBlk().peerBalance[peerId]
        if currentBalance <= 0:
            self.schedule_transaction_generation(peerId)
            return
        amt = random.randint(1, currentBalance)
        receiverId = random.choice([id for id in range(len(self.peers)) if id != peerId])

        txn = Transaction(peerId, receiverId, amt)

        self.peers[peerId].add_txn_in_mempool(txn)

        for connectedPeerId in self.peers[peerId].connectedPeers:
            self.schedule_transaction_propagation(peerId, connectedPeerId, txn)

        self.schedule_transaction_generation(peerId)
    ## Transaction Generation Ends
    ################################################


    ################################################
    ## Transaction Propogation Begins
    def schedule_transaction_propagation(self, senderId: int, receiverId: int, txn: Transaction):
        """Schedules the propagation of the transaction from sender to receiver."""
        pij = self.peers[senderId].pij[receiverId]
        cij = self.peers[senderId].cij[receiverId]
        dij = random.expovariate(lambd=cij/96)
        delay = pij + Transaction.size / cij  + dij
        delay = delay / 1000 ## delay in seconds

        event = Event(EventType.TRANSACTION_PROPAGATE, self.env.now + delay, senderId, receiverId, transaction=txn)
        self.env.process(self.schedule_event(event, delay=delay))

    def process_transaction_propagation(self, event: Event):
        """
        Processes the transaction propagation event.

        Checks if the transaction has been seen before for correct loopless forwarding implementation.
        Transaction is not verified here, as the creator might be not a different branch of the tree (hence have different balance).
        Transaction is verified while adding to a block.
        Propagates transaction to connected peers. (Loopless forwarding)
        """
        peerId = event.peerId
        if self.peers[peerId].transaction_seen(event.transaction):
            return
        
        txn = event.transaction

        self.peers[peerId].add_txn_in_mempool(txn)
        
        for connectedPeerId in self.peers[peerId].connectedPeers:
            if connectedPeerId == event.senderPeerId:
                continue
            self.schedule_transaction_propagation(peerId, connectedPeerId, txn)
    ## Transaction Propogation Ends
    ############################################



def run_simulation(peers, block_interarrival_time: float, transaction_interarrival_time: float, sim_time: float):
    env = simpy.Environment()
    simulator = EventSimulator(env, peers, block_interarrival_time, transaction_interarrival_time, sim_time)

    env.run(until=sim_time)
