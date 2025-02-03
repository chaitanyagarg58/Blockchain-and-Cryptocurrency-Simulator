#include<iostream>
#include "eventManager.cpp"
using namespace std;


int main(int argc, char* argv[]){
    if (argc != 4){
        std::cerr << "Usage : ./a.out [Number of peers] [Z0] [Z1]" << std::endl; 
        exit(1);
    }

    int num_of_peers = stoi(argv[1]);
    float z0 = stof(argv[2]);
    float z1 = stof(argv[3]);
    
    // cout << num_of_peers << " " << z0 << " " << z1 << endl;
    EventManager em(num_of_peers);
}