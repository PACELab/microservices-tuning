#ifndef SOCIAL_NETWORK_MICROSERVICES_GLOBALS_H
#define SOCIAL_NETWORK_MICROSERVICES_GLOBALS_H

#include<thread>

unsigned int HW_THREADS = std::thread::hardware_concurrency();
//unsigned int HW_THREADS = 48; 
float WORKER_THREAD_FACTOR = 25;
unsigned int LOG_DURATION = 1000; //in milliseconds
unsigned int WRITE_TIMELINE_NUM_WORKERS = HW_THREADS;
#endif
