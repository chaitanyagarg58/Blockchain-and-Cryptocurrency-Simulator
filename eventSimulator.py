import simpy
from event import EventType, Event
from peer import NetworkType, CPUType, PeerNode
from transaction import Transaction
import random


class EventSimulator:
    def __init__(self, env: simpy.Environment, peers: list[PeerNode], transaction_mean_time: float):
        self.env = env
        self.peers = peers
        self.transaction_mean_time = transaction_mean_time

        self.eventHandler = {}
        self.eventHandler[EventType.BLOCK_GENERATE] = self.process_block_generation
        self.eventHandler[EventType.BLOCK_PROPAGATE] = self.process_block_propagation
        self.eventHandler[EventType.TRANSACTION_GENERATE] = self.process_transaction_generation
        self.eventHandler[EventType.TRANSACTION_PROPAGATE] = self.process_transaction_propagation

        for peer in peers:
            self.schedule_transaction_generation(peer.peerId)

    def process_event(self, event: Event):
        # curr_time = self.env.now
        eventType = event.etype
        handler = self.eventHandler.get(event.etype, None)
        if handler:
            handler(event)
        else:
            print(f"Unkown Event Type {eventType}")


    def schedule_event(self, event: Event, delay: float):
        yield self.env.timeout(delay)
        self.process_event(event)


    def process_block_generation(self, event: Event):
        # check last blkid field of peer and then decide to terminate or actually add
        # if adding, then create another block gen event and block_prop event to all adjacent nodes
   
        self.env.process(self.schedule_event(Event(), delay=0)) # sample for how to schedule new event
        pass

    def process_block_propagation(self, event: Event):
        pass
    
    def schedule_transaction_generation(self, peerId: int):
        delay = random.expovariate(lambd=self.transaction_mean_time)
        event = Event(EventType.TRANSACTION_GENERATE, self.env.now + delay, None, peerId)
        self.env.process(self.schedule_event(event, delay=delay))

    def process_transaction_generation(self, event: Event):
        peerId = event.peerId
        currentBalance = self.peers[peerId].currentBalance
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


    def schedule_transaction_propagation(self, senderId: int, receiverId: int, txn: Transaction):
        delay = 0 #### TODO sample using propagation formula given

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



def run_simulation(peers, transaction_mean_time: float, sim_time: int):
    env = simpy.Environment()
    simulator = EventSimulator(env, peers, transaction_mean_time)
    # event = None
    # env.process(simulator.schedule_event(event, delay=0))

    env.run(until=sim_time)
    print("Simulation Complete")