#ifndef SOCIAL_NETWORK_MICROSERVICES_GLOBALS_H
#define SOCIAL_NETWORK_MICROSERVICES_GLOBALS_H

#include<thread>

unsigned int HW_THREADS = std::thread::hardware_concurrency();
int WORKER_THREAD_FACTOR = 20;
unsigned int LOG_DURATION = 1000; //in milliseconds
#endif
