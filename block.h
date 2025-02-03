#include "transaction.h"
#include <set>

using namespace std;

class block{

public:

    int BlkID;
    int creatorID;
    int size;
    set<Transaction> Txns;

    int prevBlkID;
    
    
}