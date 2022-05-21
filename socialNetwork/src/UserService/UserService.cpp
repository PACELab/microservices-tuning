#include <thrift/protocol/TBinaryProtocol.h>
#include <thrift/server/TThreadedServer.h>
#include <thrift/transport/TServerSocket.h>
#include <thrift/transport/TBufferTransports.h>
#include <thrift/concurrency/PlatformThreadFactory.h>
#include <thrift/concurrency/ThreadManager.h>
#include <thrift/server/TNonblockingServer.h>
#include <thrift/transport/TNonblockingServerSocket.h>
#include <string.h>

#include <signal.h>
#include <chrono>
#include <thread>

#include "../globals.h"
#include "../utils.h"
#include "../utils_memcached.h"
#include "../utils_mongodb.h"
#include "UserHandler.h"

using namespace apache::thrift::server;
using namespace apache::thrift;
using namespace apache::thrift::transport;
using namespace apache::thrift::protocol;
using namespace social_network;
using namespace apache::thrift::concurrency;
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

  int io_threads = HW_THREADS / 2 + 1 ;
  size_t worker_threads = HW_THREADS * WORKER_THREAD_FACTOR + 1;
  int port = config_json["user-service"]["port"];
  std::string compose_post_addr = config_json["compose-post-service"]["addr"];
  int compose_post_port = config_json["compose-post-service"]["port"];
  std::string social_graph_addr = config_json["social-graph-service"]["addr"];
  int social_graph_port = config_json["social-graph-service"]["port"];

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

  ClientPool<ThriftClient<ComposePostServiceClient>> compose_post_client_pool(
      "compose-post", compose_post_addr, compose_post_port, 0, 128, 1000);

  ClientPool<ThriftClient<SocialGraphServiceClient>> social_graph_client_pool(
      "social-graph", social_graph_addr, social_graph_port, 0, 128, 1000);

  mongoc_client_t *mongodb_client = mongoc_client_pool_pop(mongodb_client_pool);
  if (!mongodb_client) {
    LOG(fatal) << "Failed to pop mongoc client";
    return EXIT_FAILURE;
  }
  bool r = false;
  while (!r) {
    r = CreateIndex(mongodb_client, "user", "user_id", true);
    if (!r) {
      LOG(error) << "Failed to create mongodb index, try again";
      sleep(1);
    }
  }
  mongoc_client_pool_push(mongodb_client_pool, mongodb_client);

 stdcxx::shared_ptr<PlatformThreadFactory> threadFactory
        = stdcxx::shared_ptr<PlatformThreadFactory>(new PlatformThreadFactory());
 // Change the io_thread and worker_thread number based on the configuration selected                   
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
           }                                                                                            
           if( strncmp(line.c_str(), worker_threads_prefix.c_str(), worker_threads_prefix.size()) == 0) 
           {                                                                                            
                   pos = line.find(delimiter) ;                                                         
                   worker_threads = stoi(line.substr(pos+1, 100));                                      
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
              &compose_post_client_pool,
              &social_graph_client_pool)),  
        std::make_shared<TBinaryProtocolFactory>(),
          std::make_shared<TNonblockingServerSocket>("0.0.0.0",port),
          threadManager);
  server.setNumIOThreads(io_threads);
  std::cout << "Starting the user-service server (non blocking server) ..." << std::endl;
  server.serve();
/*  std::thread server_thread(std::bind(&TNonblockingServer::serve, &server));
  while(1)
  {
          std::this_thread::sleep_for(std::chrono::milliseconds(LOG_DURATION));
          std::cout << "Total task:"<< threadManager->totalTaskCount() << "Pending task: " << threadManager->pendingTaskCount() << std::endl;
  }
*/
}
