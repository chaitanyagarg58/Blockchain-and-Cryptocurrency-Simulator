#include "utilities.h"
#include <priority_queue>
using namespace std;

#define MIN_DEGREE 3
#define MAX_DEGREE 6


class Network{
public:
    vector<vector<int>> edges;
    int num_of_peers;
    vector<bool> seen;
    vector<int> degree;

    Network(int num_peers):num_of_peers{num_peers}{
        edges.resize(num_of_peers+1);
        seen.resize(num_of_peers+1);
        degree.resize(num_of_peers+1);
    }

    void isConnected(int node){
        if(seen[node])return;
        for(auto &c:edges[node]){
            if(seen[c])continue;
            seen[c] = true;
            isConnected(c);
        }
    }

    int generate_random_degree(){
        random_device rd; 
        mt19937 gen(rd());

        uniform_int_distribution<> distr(MIN_DEGREE, MAX_DEGREE);
        return distr(gen);
    }

    bool check_degree_sequence(){
        int s = 0;
        for(int i=1;i<=num_of_peers;i++){
            s += degree[i];
        }
        if(s % 2 != 0)return(false);
        int pref = 0, suf = 0;
        for(int i=2;i<=num_of_peers;i++){
            suf += min(degree[i], )
        }
    }


    bool create_graph(){
        for(int i=1;i<=num_of_peers;i++){
            degree[i] = generate_random_degree();
        }

        if(check_degree_sequence() == false)return(false);

        seen.assign(num_of_peers, false);
        isConnected(1);
        bool created = true;
        for(int i=1;i<=num_of_peers;i++){
            if(seen[i] == true)continue;
            else {created = false;break;}
        }

        if(!created)return(false);
        else return(true);
    }

    void start_graph_generation(){
        while !create_graph(){;}
    }
};
