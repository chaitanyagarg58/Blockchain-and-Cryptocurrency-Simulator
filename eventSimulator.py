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
        self.pij = [[0] * len(peers) for _ in range(len(peers))]
        self.cij = [[0] * len(peers) for _ in range(len(peers))]

        for p1 in peers:
            for p2 in p1.pij:
                self.pij[p1.peerId][p2] = p1.pij[p2]
            for p2 in p1.cij:
                self.cij[p1.peerId][p2] = p1.cij[p2]

        for peer in peers:
            self.schedule_transaction_generation(peer.peerId)
            self.schedule_block_generation(peer.peerId)
        self.cnt = 0

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
        if self.cnt < self.env.now:
            print(self.env.now)
            self.cnt += 1
        self.process_event(event)

    #############################################
    ## BLOCK Generation Starts
    def schedule_block_generation(self, peerId:int):
        delay = random.expovariate(lambd= self.peers[peerId].hashingPower / self.block_interarrival_time)

        lastBlock = self.peers[peerId].get_lastBlk()
    
        txnList = self.peers[peerId].sample_transactions()
        parentBlkId = lastBlock.BlkID
        parentBlkBalance = lastBlock.peerBalance
        depth = lastBlock.depth + 1

        cpu = 0
        net = 0
        if self.peers[peerId].cpuType == CPUType.HIGH:
            cpu = 1
        if self.peers[peerId].netType == NetworkType.FAST:
            net = 1

        block = Block(creatorId=peerId, txns=txnList, parentBlockId=parentBlkId, parentBlockBalance=parentBlkBalance, depth=depth, cpu = cpu, net = net)
        self.peers[peerId].set_miningBlk(parentBlkId)

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
    ## BLOCK Generation Ends
    ##############################################


    ###############################################
    ## BLOCK Propagation Starts
    def schedule_block_propagation(self, senderId: int, receiverId: int, block: Block):
        #### TODO sample using propagation formula given -> Done
        # pij = self.peers[senderId].pij[receiverId]
        # cij = self.peers[senderId].cij[receiverId]
        pij = self.pij[senderId][receiverId]
        cij = self.cij[senderId][receiverId]
        # assert pij == pij1
        # assert cij == cij1
        dij = random.expovariate(lambd=cij/96)
        delay = pij + block.size / cij  + dij
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
        delay = random.expovariate(lambd=1/self.transaction_mean_time)
        event = Event(EventType.TRANSACTION_GENERATE, self.env.now + delay, None, peerId)
        self.env.process(self.schedule_event(event, delay=delay))

    def process_transaction_generation(self, event: Event):
        peerId = event.peerId
        currentBalance = self.peers[peerId].get_lastBlk().peerBalance[peerId]
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
        dij = random.expovariate(lambd=cij/96)
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
