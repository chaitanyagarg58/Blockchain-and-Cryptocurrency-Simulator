import simpy
from event import EventType, Event
from peer import NetworkType, CPUType, PeerNode
from transaction import Transaction
from block import Block
import random
from typing import List


class EventSimulator:
    def __init__(self, env: simpy.Environment, peers: List['PeerNode'], block_interarrival_time: float, transaction_mean_time: float):
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

    def process_event(self, event: Event):
        eventType = event.etype
        handler = self.eventHandler.get(event.etype, None)
        if handler:
            handler(event)
        else:
            print(f"Unkown Event Type {eventType}")


    def schedule_event(self, event: Event, delay: float):
        yield self.env.timeout(delay)
        ## TODO : Create a log file code for manual checking
        self.process_event(event)

    #############################################
    ## BLOCK Generation Starts
    def schedule_block_generation(self, peerId:int):
        delay = random.expovariate(lambd=self.block_interarrival_time / self.peers[peerId].hashingPower)
        
        lastBlock = self.peers[peerId].get_lastBlk()
    
        txnList = self.peers[peerId].sample_transactions()
        parentBlkId = lastBlock.BlkID
        parentBlkBalance = lastBlock.peerBalance
        depth = lastBlock.depth + 1
        
        block = Block(creatorId=peerId, txns=txnList, parentBlockId=parentBlkId, parentBlockBalance=parentBlkBalance, depth=depth)

        event = Event(EventType.BLOCK_GENERATE, self.env.now + delay, None, peerId, block=block)
        self.env.process(self.schedule_event(event, delay=delay))

    def process_block_generation(self, event: Event):
        # check last blkid field of peer and then decide to terminate or actually add
        # if adding, then create another block gen event and block_prop event to all adjacent nodes
        peerId = event.peerId
        block = event.block

        if self.peers[peerId].get_lastBlk().BlkID != block.parentBlkID:
            return

        self.peers[peerId].add_block(block, self.env.now)

        for connectedPeerId in self.peers[peerId].connectedPeers:
            self.schedule_block_propagation(peerId, connectedPeerId, block)

        self.schedule_block_generation(peerId)
        self.env.process(self.schedule_event(Event(), delay=0)) # sample for how to schedule new event
    ## BLOCK Generation Ends
    ##############################################


    ###############################################
    ## BLOCK Propagation Starts
    def schedule_block_propagation(self, senderId: int, receiverId: int, block: Block):
        #### TODO sample using propagation formula given -> Done
        pij = self.peers[senderId].pij[receiverId]
        cij = self.peers[senderId].cij[receiverId]
        dij = random.expovariate(lambd=96/cij)
        delay = pij + Transaction.size / cij  + dij
        delay = delay / 1000 ## delay in seconds

        event = Event(EventType.BLOCK_PROPAGATE, self.env.now + delay, senderId, receiverId, block=block)
        self.env.process(self.schedule_event(event, delay=delay))


    def process_block_propagation(self, event: Event):
        ## Need to verify block here
        peerId = event.peerId
        if self.peers[peerId].block_seen(event.block):
            return
        
        block = event.block

        self.peers[peerId].add_block(block, self.env.now)
        
        for connectedPeerId in self.peers[peerId].connectedPeers:
            if connectedPeerId == event.senderPeerId:
                continue
            self.schedule_block_propagation(peerId, connectedPeerId, block)
    ## BLOCK Propagation Ends
    ##############################################



    ###############################################
    ## Transaction Generation Starts
    def schedule_transaction_generation(self, peerId: int):
        delay = random.expovariate(lambd=self.transaction_mean_time)
        event = Event(EventType.TRANSACTION_GENERATE, self.env.now + delay, None, peerId)
        self.env.process(self.schedule_event(event, delay=delay))

    def process_transaction_generation(self, event: Event):
        peerId = event.peerId
        currentBalance = self.peers[peerId].get_lastBlk().peerBalance
        if currentBalance <= 0:
            self.schedule_transaction_generation(peerId)
            return
        amt = random.randint(1, currentBalance)
        receiverId = random.choice([id for id in range(len(self.peers)) if id != peerId])

        txn = Transaction(peerId, receiverId, amt)

        self.peers[peerId].add_txn_in_mempool(txn)

        ## TODO add event to propagate txn to connected peers -> DONE
        for connectedPeerId in self.peers[peerId].connectedPeers:
            self.schedule_transaction_propagation(peerId, connectedPeerId, txn)

        self.schedule_transaction_generation(peerId)
    ## Transaction Generation Ends
    ################################################

    ################################################
    ## Transaction Propogation Begins
    def schedule_transaction_propagation(self, senderId: int, receiverId: int, txn: Transaction):
        #### TODO sample using propagation formula given -> Done
        pij = self.peers[senderId].pij[receiverId]
        cij = self.peers[senderId].cij[receiverId]
        dij = random.expovariate(lambd=96/cij)
        delay = pij + Transaction.size / cij  + dij
        delay = delay / 1000 ## delay in seconds

        event = Event(EventType.TRANSACTION_PROPAGATE, self.env.now + delay, senderId, receiverId, transaction=txn)
        self.env.process(self.schedule_event(event, delay=delay))

    
    def process_transaction_propagation(self, event: Event):
        ## Do not need to verify transactions here as we might be on some other branch than the creator of transaction
        ## Will verify transaction only in block creation
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



def run_simulation(peers, block_interarrival_time: float, transaction_mean_time: float, sim_time: int):
    env = simpy.Environment()
    simulator = EventSimulator(env, peers, block_interarrival_time, transaction_mean_time)
    # event = None
    # env.process(simulator.schedule_event(event, delay=0))

    env.run(until=sim_time)
    print("Simulation Complete")
