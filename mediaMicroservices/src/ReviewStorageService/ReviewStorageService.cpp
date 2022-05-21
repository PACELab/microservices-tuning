#include <thrift/protocol/TBinaryProtocol.h>
#include <thrift/server/TThreadedServer.h>
#include <thrift/transport/TServerSocket.h>
#include <thrift/transport/TBufferTransports.h>
#include "nlohmann/json.hpp"
#include <thrift/concurrency/PlatformThreadFactory.h>
#include <thrift/concurrency/ThreadManager.h>
#include <thrift/server/TNonblockingServer.h>
#include <thrift/transport/TNonblockingServerSocket.h>
#include <signal.h>
#include <iostream>
#include <fstream>
#include <string.h>


#include "../globals.h"
#include "../utils.h"
#include "../utils_mongodb.h"
#include "../utils_memcached.h"
#include "ReviewStorageHandler.h"

using apache::thrift::server::TThreadedServer;
using apache::thrift::transport::TServerSocket;
using apache::thrift::transport::TFramedTransportFactory;
using apache::thrift::protocol::TBinaryProtocolFactory;
using namespace apache::thrift::server;
using namespace apache::thrift;
using namespace apache::thrift::transport;
using namespace apache::thrift::protocol;
using namespace apache::thrift::concurrency;
using namespace media_service;
using namespace std;


static memcached_pool_st* memcached_client_pool;
static mongoc_client_pool_t* mongodb_client_pool;

void sigintHandler(int sig) {
  if (memcached_client_pool != nullptr) {
    memcached_pool_destroy(memcached_client_pool);
  }
  if (mongodb_client_pool != nullptr) {
    mongoc_client_pool_destroy(mongodb_client_pool);
  }
  exit(EXIT_SUCCESS);
}

int main(int argc, char *argv[]) {
  signal(SIGINT, sigintHandler);

  init_logger();

  SetUpTracer("config/jaeger-config.yml", "review-storage-service");

  json config_json;
  if (load_config_file("config/service-config.json", &config_json) != 0) {
    exit(EXIT_FAILURE);
  }

  int port = config_json["review-storage-service"]["port"];

  memcached_client_pool =
      init_memcached_client_pool(config_json, "review-storage",
          MEMCACHED_POOL_MIN_SIZE, MEMCACHED_POOL_MAX_SIZE);
  mongodb_client_pool = init_mongodb_client_pool(config_json, "review-storage",
      MONGODB_POOL_MAX_SIZE);

  if (memcached_client_pool == nullptr || mongodb_client_pool == nullptr) {
    return EXIT_FAILURE;
  }
  int io_threads = HW_THREADS / 4 + 1 ;
  size_t worker_threads = HW_THREADS * WORKER_THREAD_FACTOR;
  stdcxx:shared_ptr<PlatformThreadFactory> threadFactory = stdcxx:: shared_ptr<PlatformThreadFactory>(new PlatformThreadFactory());
  string ms_prefix = "review-storage-service";
  ifstream config_file("config/parameters-config.txt");
  string io_threads_prefix = ms_prefix + "_io_threads";
  string worker_threads_prefix = ms_prefix + "_worker_threads";
  string delimiter = ",";
  string line;
  size_t pos;

if (config_file.is_open())
{
  while ( getline(config_file,line) )
  {
          if( strncmp(line.c_str(), io_threads_prefix.c_str(), io_threads_prefix.size()) == 0)
          {
                  pos = line.find(delimiter);
                  io_threads = stoi(line.substr(pos+1, 100));
                  cout << "IO threads " << io_threads << "\n";
          }
          if( strncmp(line.c_str(), worker_threads_prefix.c_str(), worker_threads_prefix.size()) == 0)
          {
                  pos = line.find(delimiter) ;
                  worker_threads = stoi(line.substr(pos+1, 100));
                  cout << "worker threads " << worker_threads << "\n";
          }
  }
  config_file.close();
}
   stdcxx::shared_ptr<ThreadManager> threadManager = ThreadManager::newSimpleThreadManager(worker_threads);
   threadManager->threadFactory(threadFactory);
   threadManager->start();


   TNonblockingServer server(
         std::make_shared<ReviewStorageServiceProcessor>(
           std::make_shared<ReviewStorageHandler>(
               memcached_client_pool, mongodb_client_pool)),
           std::make_shared<TBinaryProtocolFactory>(),
           std::make_shared<TNonblockingServerSocket>("0.0.0.0",port),
           threadManager);
   server.setNumIOThreads(io_threads);
   std::cout << "Starting the cast-info-service server (non blocking server) ..." << std::endl;
   server.serve();

}
