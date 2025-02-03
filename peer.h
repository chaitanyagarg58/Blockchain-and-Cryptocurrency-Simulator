#include <iostream>
#include <vector>
#include "blockchain.h"
using namespace std;

enum class NetworkType {
    SLOW,
    FAST,
};

enum class CPUType{
    LOW,
    HIGH,
};


class PeerNode{
private:
    int peerId;
    NetworkType netType;
    CPUType cpuType;
    double hash_power;
    Node* blockchain;
    vector<int> connectedPeer;
    int lastBlkId; // last block id of the current longest chain considered
public:
    PeerNode(int);

    long 
};