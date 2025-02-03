#include "eventManager.h"
#include<fstream>

using namespace std;


EventManager::EventManager(int num_of_peers){
    for (int i = 1; i <= num_of_peers; i++){
        this->peerMap[i] = new PeerNode(i);
        this->eventQueue.push(new Event());
    }

    //  Reading of graph data file for the network graph following the constraint of >= 3 neighbors and <= 6 neighbors for each node
    string file_name = "graph_data.txt"
    std::ifstream file(file_name);  // Open the file for reading
    int num, vtx1, vtx2; 

    // checking whether file exists or not
    if (file.is_open()) {
        file >> num;
        //sanity check of nodes in the graph matching with the number_of_peers
        if(num1 != num_of_peers){
            std::cerr << "Wrong Graph in graph file" << std::endl;
            exit(1);
        }

        while (file >> vtx1) {  // Read integers one by one
            file >> vtx2;
            // appending the undirected graph edge in the adjacency list of vtx1 and vtx2
            this->peerMap[vtx1]->connectedPeer.push_back(vtx2); 
            this->peerMap[vtx2]->connectedPeer.push_back(vtx1);
        }
        file.close();
    } else {
        std::cerr << "Unable to open graph file!" << std::endl;
        exit(1);
    }
}



void EventManager::run_event(Event* e){
    switch(e->EventType){
        case BLOCK_GENERATE:
            // check last blkid field of peer and then decide to terminate or actually add
            // if adding, then create another block gen event and block_prop event to all adjacent nodes
            


        case BLOCK_PROPAGATE:
            // 

        case TRANSACTION_GENERATE:

        case TRANSACTION_PROPAGATE

        
        default: 
            cout << "Unknown event type" << endl;
            break;
    }


}