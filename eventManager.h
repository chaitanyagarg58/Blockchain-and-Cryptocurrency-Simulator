#include <iostream>
#include <priority_queue>
#include <unordered_map>
#include "peer.h"
#include "event.h"
using namespace std;



class EventManager{
private:
    unordered_map<int, PeerNode *> peerMap;
    priority_queue<Event *> eventQueue;

public:
    EventManager(int);
    void run_event()
};