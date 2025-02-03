#include <iostream>
#include "utilities.h"

using namespace std;

enum EventType {
    BLOCK_GENERATE,
    BLOCK_PROPAGATE,
    TRANSACTION_GENERATE,
    TRANSACTION_PROPAGATE,
} 

class Event{
private:
    EventType etype;
    int timestamp;
    int senderPeerId;
    int peerId;
    Block* b;
    transaction* t;


};