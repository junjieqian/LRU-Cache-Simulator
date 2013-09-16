/* cache-simulator.cc
 *
 */

#include <unordered_map>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#define memory_time  50   // cycles used to commute with memory
#define n_way  2          // if it is associative, size of each set

using namespace std;

int cycles=0;
int hit=0;
int miss=0;
int cachesize=8388608;            // cache blocks
int mappingStrat=3;

typedef boost::unordered_map<long, int> map;

class Cache {
    private:
        map cacheBlocks;
        map diryFlags;
        map lruValue;
        map dictSlice;
    public:
        void _init_(){
            clearcache();
        } // end initialization

        void clearcache(){
            for (int i=0; i<cachesize; i++){
                cacheBlocks[i] = 0;
                dirtyFlags[i] = 0;
                lruValue[i] = 0;
            }
        } // end clearcache function 

        int checkCacheHit(long address){
            int block = mapToBlock(address);
            if (address == cacheBlocks[block]){
                incrementLRU(block);
                return block;
            } else
                return -1;
        } // end checkCacheHit functon

        void incrementLRU(int block){
            for (int i=0; i<cachesize; i++)
                if (lruValue[i] > 0 && i!=block)
                    lruValue[i]--;
            
            if (lruValue[block] < 10)
                lruValue[block]++;
        } // end incrementLRU function

        int getLRUBlock(int start, int end){
            map lruSlice;
            int lruValues = 10000;
            for (int i=start; i<end; i++){
                lruSlice[i] = lruValue[i];
                if (lruValues > lruSlice[i])
                    lruValues = lruSlice[i];
            }
            return lruValues;
        } // end getLRUBlock

        int storeCacheBlock(long address, map biasdict){
            int blcok = mapToBlock(address);
            if (isBlockDirty(address) == 1){
                cycles += memory_time;
                dirtyFlags[block] = 0;
            }

            int returnvalue = 1;
            if (biasdict.find(cacheBlocks[block]) != biasdict.end){
                if (biasdict[cacheBlocks[block]] == 0){
                    returnvalue = -1;
                    biasdict.erase(cacheBlocks[block]);
                }
            } // end if

            cacheBlocks[block] = address;
            return returnvalue;
        } // end store cache block function

        int isBlockDirty(long address){
            int block = mapToBlock(address);
            return dirtyFlags[block];
        }

        void setDirtyFlag(long address){
            int block = mapToBlock(address);
            dirtyFlags[block] = 1;
        }

        int mapToBlock(long address){
            if (mappingStrat == 1)
                return address%cachesize;
            else if (mappingStrat == 2)
                return getLRUBlock(0, (cachesize-1));
            else if (mappingStrat == 3){
                int nway = cachesize/n_way;
                int set = address%nway;
                return getLRUBlock(set*n_way, (set*n_way)+n_way);
            }
        } // end map to block function
};

@inline
int stoi(string str){
    stringstream ss(str);
    int res;

    if (!ss>>res){
        cout << "error happens when translet string: " << str << endl;
        return -1;
    }

    return res;
}

int readBias(string intersizefile, string addressfile, unordered_map<long,int> &biasdict){
    ifstream infile(addressfile);
    if (!infile.is_open()){
        cout << "No address file exist!\n";
        return -1;
    }

    long address;
    vector<long> addr;
    while(infile>>address)
        addr.push_back(address);

    ifstream fa(intersizefile);

    if (!fa.is_open()){
        cout << "No Intersize file exist!\n";
        return -1;
    }

    string line;
    int i=0;
    while(getline(fa, line)){
        int start=1;
        int end=1;
        int size = 0;
        int cnt=0;
        while(end=line.find(',',end)){
            string sub = line.sutbstr(start, end-start+1);
            size = stoi(sub);
            start=end;
            if (size>8388608){
                biasdict[addr[i]]=cnt;
                break;
            }
            cnt++;
        }
        i++;
    } // end while loop
    return 0;
}

@inline
void helper(){
    cout << "Cache simulator calculating the percentage of BIAS objects in the cache\n";
    cout << "Usage: cachesim trace-file-path address-file-path inter-size-file-path\n";
    cout << "Cache parameters are defined in file already. \n";
    cout << "Commented the corresponding lines out, if parameters are assigned in CMDLine\n";
}

// everything starts from here
int main(int argc, char ** argv){
    if (argc<5){
        helper();
        return 0;
    }

    string tracefile     = *(argv+1);
    string addressfile   = *(argv+2);
    string intersizefile = *(argv+3);
    long cnt              = 0;  // count the cache lines having bias objects
    vector<long> count;         // vector used to store the cnt

    unordered_map<long, int> biasdict;
    if(!readBias(intersizefile, addressfile, biasdict)){
        cout << "Failed to read the bias\n";
        helper();
        return 0;
    }

    Cache *cache = new Cache();
    cache->_init_();

    ifstream infile(tracefile);
    if (!infile.is_open()){
        cout << "Failed to open trace file\n";
        helper();
        return 0;
    }

    long address;
    int mode;
    int size;
    while(infile>>address>>mode>>size){
        int cachehit;
        cachehit = cache->checkCacheHit(address);

        if (biasdict.find(address) != biasdict.end()){
            if (biasdict[address]>0)
                biasdict[address]--;
            else{
                biasdict[address]--;
                cnt++;
                count.push_back(cnt);
            }
        } // end if bias disct has this key

        if (mode==0){
            if (cachehit>0){
                hit++;
                cycles++;
            } // end hit else
            else{
                miss++;
                cycles+=memory_time;
                if (cache->storeCacheBlock(address, biasdict)<0){
                    cnt--;
                    count.push_back(cnt);
                } // end if
            }  //end else miss
        } // end read if

        else if (mode==1){
            if (writeStrat==1){
                if (cachehit>0){
                    hit++;
                    cycles+=memory_time;
                }
                else{
                    miss++;
                    cycles+=memory_time;
                    if(cache->storeCacheBlock(address,biasdict)<0){
                        cnt--;
                        count.push_back(cnt);
                    }
                }
            } // end write through strategy
            else if(writeStrat==2){
                if (cachehit>0){
                    hit++;
                    cycles+=1;
                    cache->setDirtyFlag(address);
                } else {
                    miss++;
                    cycles+=1;
                    if (cache->storeCacheBlock(address,biasdict)<0){
                        cnt--;
                        count.push_back(cnt);
                    }
                    cache->setDirtyFlag(address);
                }
            } // end write back strategy
        } // end write if
    } // end file reading in

    infile.close();

    ofstream outfile("bias-occupation-cache");
    for(int ii=0;ii<count.size();ii++)
        outfile<<count[ii]<<endl;
    outfile.close();
    return 0;
}