//
// Created by 李鑫烨 on 2017/12/21.
//
#include <bitset>

using namespace std;

#define LENGTH 11111431

#ifndef BLOOMFILTER_BLOOMFILTER_H
#define BLOOMFILTER_BLOOMFILTER_H

class BloomFilter {
public:
    BloomFilter();
    bool alreadyInHash(char* str);
    void addToHash(char* str);
private:
    bitset<LENGTH> hashTable;
    unsigned long DEKHash(string str);
    unsigned long DJBHash(string str);
    unsigned long ELFHash(string str);
    unsigned long JSHash(string str);
    unsigned long RSHash(string str);
};

#endif //BLOOMFILTER_BLOOMFILTER_H
