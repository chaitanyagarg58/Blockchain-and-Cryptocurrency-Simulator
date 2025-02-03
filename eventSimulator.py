import simpy
from event import EventType, Event
from peer import NetworkType, CPUType, PeerNode


class EventSimulator:
    def __init__(self, env: simpy.Environment, peers: list):
        self.env = env
        self.peers = peers

        self.eventHandler = {}
        self.eventHandler[EventType.BLOCK_GENERATE] = self.process_block_generation
        self.eventHandler[EventType.BLOCK_PROPAGATE] = self.process_block_propagation
        self.eventHandler[EventType.TRANSACTION_GENERATE] = self.process_transaction_generation
        self.eventHandler[EventType.TRANSACTION_PROPAGATE] = self.process_transaction_propagation

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
    
    def process_transaction_generation(self, event: Event):
        pass
    
    def process_transaction_propagation(self, event: Event):
        pass



def run_simulation(peers, sim_time):
    env = simpy.Environment()
    simulator = EventSimulator(env, peers)
    event = None
    env.process(simulator.schedule_event(event, delay=0))

    env.run(until=sim_time)
    print("Simulation Complete")