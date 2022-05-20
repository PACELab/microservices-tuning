#include <signal.h>
#include <chrono>
#include <thread>
#include <string.h>

#include <thrift/server/TThreadedServer.h>
#include <thrift/protocol/TBinaryProtocol.h>
#include <thrift/transport/TServerSocket.h>
#include <thrift/transport/TBufferTransports.h>
#include <thrift/concurrency/PlatformThreadFactory.h>
#include <thrift/concurrency/ThreadManager.h>
#include <thrift/server/TNonblockingServer.h>
#include <thrift/transport/TNonblockingServerSocket.h>

#include "../globals.h"
#include "../utils.h"
#include "TextHandler.h"

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
  SetUpTracer("config/jaeger-config.yml", "text-service");

  json config_json;
  if (load_config_file("config/service-config.json", &config_json) == 0) {
    int io_threads = HW_THREADS / 2 + 1 ;
    size_t worker_threads = HW_THREADS * WORKER_THREAD_FACTOR + 1;
    int port = config_json["text-service"]["port"];
    std::string compose_addr = config_json["compose-post-service"]["addr"];
    int compose_port = config_json["compose-post-service"]["port"];

    std::string url_addr = config_json["url-shorten-service"]["addr"];
    int url_port = config_json["url-shorten-service"]["port"];

    std::string user_mention_addr = config_json["user-mention-service"]["addr"];
    int user_mention_port = config_json["user-mention-service"]["port"];

    ClientPool<ThriftClient<ComposePostServiceClient>> compose_client_pool(
        "compose-post", compose_addr, compose_port, 0, 128, 1000);

    ClientPool<ThriftClient<UrlShortenServiceClient>> url_client_pool(
        "url-shorten-service", url_addr, url_port, 0, 128, 1000);

    ClientPool<ThriftClient<UserMentionServiceClient>> user_mention_pool(
        "user-mention-service", user_mention_addr,
        user_mention_port, 0, 128, 1000);

  stdcxx::shared_ptr<PlatformThreadFactory> threadFactory
        = stdcxx::shared_ptr<PlatformThreadFactory>(new PlatformThreadFactory());
  // Change the io_thread and worker_thread number based on the configuration selected
  string ms_prefix = "text-service";
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
        std::make_shared<TextServiceProcessor>(
            std::make_shared<TextHandler>(
                &compose_client_pool,
                &url_client_pool,
                &user_mention_pool)),
          std::make_shared<TBinaryProtocolFactory>(),
          std::make_shared<TNonblockingServerSocket>("0.0.0.0",port),
          threadManager);
  server.setNumIOThreads(io_threads);
  std::cout << "Starting the text-service server (non blocking server) ..." << std::endl;
  server.serve();
  /*
  std::thread server_thread(std::bind(&TNonblockingServer::serve, &server));
  while(1)
  {
          std::this_thread::sleep_for(std::chrono::milliseconds(LOG_DURATION));
          std::cout << "Total task:"<< threadManager->totalTaskCount() << "Pending task: " << threadManager->pendingTaskCount() << std::endl;
  }

  */
  } 
  else exit(EXIT_FAILURE);
}


