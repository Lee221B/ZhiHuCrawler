//
// Created by 李鑫烨 on 2017/12/21.
//

#include "BloomFilter.h"

BloomFilter::BloomFilter() {
    hashTable &= 0;
}

bool BloomFilter::alreadyInHash(char str[100]) {
    long hash[5];
	string str_temp(str);
    hash[0] = DEKHash(str_temp) % LENGTH;
    hash[1] = DJBHash(str_temp) % LENGTH;
    hash[2] = ELFHash(str_temp) % LENGTH;
    hash[3] = JSHash(str_temp) % LENGTH;
    hash[4] = RSHash(str_temp) % LENGTH;
    for(int i = 0; i < 5; i++) {
        if(!hashTable.test(hash[i]))
            return false;
    }
    return true;
 }

void BloomFilter::addToHash(char str[100]) {
    unsigned long hash[5];
	string str_temp(str);
    hash[0] = DEKHash(str_temp) % LENGTH;
    hash[1] = DJBHash(str_temp) % LENGTH;
    hash[2] = ELFHash(str_temp) % LENGTH;
    hash[3] = JSHash(str_temp) % LENGTH;
    hash[4] = RSHash(str_temp) % LENGTH;
    for(int i = 0; i < 5; i++) {
		//printf("hash[%d]: %lu\n", i, hash[i]);
        hashTable.set(hash[i]);
    }
}

unsigned long BloomFilter::DJBHash(string str){
    unsigned long hash = 5381;
    for(int i = 0; i < str.length(); i++) {
        hash = ((hash << 5) + hash) + str[i];
    }
    return hash;
}

unsigned long BloomFilter::ELFHash(string str){
    unsigned long hash = 0;
    unsigned long x = 0;
    for(int i = 0; i < str.length(); i++) {
        hash = (hash << 4) + str[i];
        if((x & 0xf0000000) != 0) {
            hash ^= (x >> 24);
        }
        hash &= ~x;
    }
    return hash;
}

unsigned long BloomFilter::JSHash(string str) {
    unsigned long hash = 1315423911;
    for(int i = 0; i < str.length(); i++) {
        hash ^= ((hash << 5) + str[i] + (hash >> 2));
    }
    return hash;
}

unsigned long BloomFilter::RSHash(string str) {
    unsigned long b = 378551;
    unsigned long a = 63689;
    unsigned long hash = 0;
    for(int i = 0; i < str.length(); i++) {
        hash = hash * a + str[i];
        a *= b;
    }
	return hash;
}

unsigned long BloomFilter::DEKHash(string str) {
    unsigned long hash = str.length();
    for(int i = 0; i < str.length(); i++) {
        hash = ((hash << 5) ^ (hash >> 27)) ^ str[i];
    }
    return hash;
}
