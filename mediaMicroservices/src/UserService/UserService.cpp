#include <thrift/protocol/TBinaryProtocol.h>
#include <thrift/server/TThreadedServer.h>
#include <thrift/transport/TServerSocket.h>
#include <thrift/transport/TBufferTransports.h>
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
#include "../utils_memcached.h"
#include "../utils_mongodb.h"
#include "UserHandler.h"

using apache::thrift::server::TThreadedServer;
using apache::thrift::transport::TServerSocket;
using apache::thrift::transport::TFramedTransportFactory;
using apache::thrift::protocol::TBinaryProtocolFactory;
using media_service::UserHandler;
 using namespace apache::thrift::server;
 using namespace apache::thrift;
 using namespace apache::thrift::transport;
 using namespace apache::thrift::protocol;
 using namespace apache::thrift::concurrency;
 using namespace media_service;
 using namespace std;


void sigintHandler(int sig) {
  exit(EXIT_SUCCESS);
}

int main(int argc, char *argv[]) {
  signal(SIGINT, sigintHandler);
  init_logger();

  SetUpTracer("config/jaeger-config.yml", "user-service");

  json config_json;
  if (load_config_file("config/service-config.json", &config_json) != 0) {
    exit(EXIT_FAILURE);
  }

  std::string secret = config_json["secret"];

  int port = config_json["user-service"]["port"];
  std::string compose_addr = config_json["compose-review-service"]["addr"];
  int compose_port = config_json["compose-review-service"]["port"];

  memcached_pool_st *memcached_client_pool =
      init_memcached_client_pool(config_json, "user", 32, 128);
  mongoc_client_pool_t *mongodb_client_pool =
      init_mongodb_client_pool(config_json, "user", 128);

  if (memcached_client_pool == nullptr || mongodb_client_pool == nullptr) {
    return EXIT_FAILURE;
  }

  std::string machine_id;
  if (GetMachineId(&machine_id) != 0) {
    exit(EXIT_FAILURE);
  }

  std::mutex thread_lock;

  ClientPool<ThriftClient<ComposeReviewServiceClient>> compose_client_pool(
      "compose-review-client", compose_addr, compose_port, 0, 128, 1000);
  int io_threads = HW_THREADS / 4 + 1 ;
  size_t worker_threads = HW_THREADS * WORKER_THREAD_FACTOR;
  stdcxx:shared_ptr<PlatformThreadFactory> threadFactory = stdcxx:: shared_ptr<PlatformThreadFactory>(new PlatformThreadFactory());
  string ms_prefix = "user-service";
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
         std::make_shared<UserServiceProcessor>(
           std::make_shared<UserHandler>(
                &thread_lock,                        
                machine_id,                          
                secret,                              
                memcached_client_pool,               
                mongodb_client_pool,                 
                &compose_client_pool)),              
           std::make_shared<TBinaryProtocolFactory>(),
           std::make_shared<TNonblockingServerSocket>("0.0.0.0",port),
           threadManager);
   server.setNumIOThreads(io_threads);
   std::cout << "Starting the cast-info-service server (non blocking server) ..." << std::endl;
   server.serve();


}
