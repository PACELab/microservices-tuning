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
#include "ComposeReviewHandler.h"
#include "../utils.h"
#include "../utils_memcached.h"

using json = nlohmann::json;
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

void sigintHandler(int sig) {
  exit(EXIT_SUCCESS);
}

int main(int argc, char *argv[]) {
  signal(SIGINT, sigintHandler);
  init_logger();

  SetUpTracer("config/jaeger-config.yml", "compose-review-service");

  json config_json;
  if (load_config_file("config/service-config.json", &config_json) != 0) {
    exit(EXIT_FAILURE);
  }

  int port = config_json["compose-review-service"]["port"];
  std::string review_storage_addr =
      config_json["review-storage-service"]["addr"];
  int review_storage_port = config_json["review-storage-service"]["port"];

  std::string user_review_addr = config_json["user-review-service"]["addr"];
  int user_review_port = config_json["user-review-service"]["port"];

  std::string movie_review_addr = config_json["movie-review-service"]["addr"];
  int movie_review_port = config_json["movie-review-service"]["port"];

  ClientPool<ThriftClient<ReviewStorageServiceClient>> compose_client_pool(
      "compose-review-service", review_storage_addr, review_storage_port, 0, 128, 1000);
  ClientPool<ThriftClient<UserReviewServiceClient>> user_client_pool(
      "user-review-service", user_review_addr, user_review_port, 0, 128, 1000);
  ClientPool<ThriftClient<MovieReviewServiceClient>> movie_client_pool(
      "movie-review-service", movie_review_addr, movie_review_port, 0, 128, 1000);


  std::string mmc_addr = config_json["compose-review-memcached"]["addr"];
  int mmc_port = config_json["compose-review-memcached"]["port"];
  std::string config_str = "--SERVER=" + mmc_addr + ":" + std::to_string(mmc_port);
  auto memcached_client = memcached(config_str.c_str(), config_str.length());
  memcached_behavior_set(memcached_client, MEMCACHED_BEHAVIOR_NO_BLOCK, 1);
  memcached_behavior_set(memcached_client, MEMCACHED_BEHAVIOR_TCP_NODELAY, 1);
  memcached_behavior_set(
      memcached_client, MEMCACHED_BEHAVIOR_BINARY_PROTOCOL, 1);
  auto memcached_client_pool = memcached_pool_create(
      memcached_client, MEMCACHED_POOL_MIN_SIZE, MEMCACHED_POOL_MAX_SIZE);

   int io_threads = HW_THREADS / 4 + 1 ;
   size_t worker_threads = HW_THREADS * WORKER_THREAD_FACTOR;
   stdcxx:shared_ptr<PlatformThreadFactory> threadFactory = stdcxx:: shared_ptr<PlatformThreadFactory>(new PlatformThreadFactory());
   string ms_prefix = "compoe-review-service";
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
          std::make_shared<ComposeReviewServiceProcessor>(
            std::make_shared<ComposeReviewHandler>(
              memcached_client_pool,
              &compose_client_pool,
              &user_client_pool,
              &movie_client_pool)),
            std::make_shared<TBinaryProtocolFactory>(),
            std::make_shared<TNonblockingServerSocket>("0.0.0.0",port),
            threadManager);
    server.setNumIOThreads(io_threads);
    std::cout << "Starting the compose-review-service server (non blocking server) ..." << std::endl;
    server.serve();


}




