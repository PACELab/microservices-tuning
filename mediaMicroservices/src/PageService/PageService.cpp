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
#include "PageHandler.h"

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

  SetUpTracer("config/jaeger-config.yml", "cast-info-service");

  json config_json;
  if (load_config_file("config/service-config.json", &config_json) != 0) {
    exit(EXIT_FAILURE);
  }

  int port = config_json["page-service"]["port"];
  std::string cast_info_addr = config_json["cast-info-service"]["addr"];
  int cast_info_port = config_json["cast-info-service"]["port"];
  std::string movie_review_addr = config_json["movie-review-service"]["addr"];
  int movie_review_port = config_json["movie-review-service"]["port"];
  std::string movie_info_addr = config_json["movie-info-service"]["addr"];
  int movie_info_port = config_json["movie-info-service"]["port"];
  std::string plot_addr = config_json["plot-service"]["addr"];
  int plot_port = config_json["plot-service"]["port"];

  ClientPool<ThriftClient<MovieInfoServiceClient>>
      movie_info_client_pool("movie-info-client", movie_info_addr,
                             movie_info_port, 0, 128, 1000);
  ClientPool<ThriftClient<CastInfoServiceClient>>
      cast_info_client_pool("cast-info-client", cast_info_addr,
                            cast_info_port, 0, 128, 1000);
  ClientPool<ThriftClient<MovieReviewServiceClient>>
      movie_review_client_pool("movie-review-client", movie_review_addr,
                               movie_review_port, 0, 128, 1000);
  ClientPool<ThriftClient<PlotServiceClient>>
      plot_client_pool("plot-client", plot_addr, plot_port, 0, 128, 1000);

   int io_threads = HW_THREADS / 4 + 1 ;
   size_t worker_threads = HW_THREADS * WORKER_THREAD_FACTOR;
   stdcxx:shared_ptr<PlatformThreadFactory> threadFactory = stdcxx:: shared_ptr<PlatformThreadFactory>(new PlatformThreadFactory());
   string ms_prefix = "page-service";
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
          std::make_shared<PageServiceProcessor>(
            std::make_shared<PageHandler>(
              &movie_review_client_pool,    
              &movie_info_client_pool,      
              &cast_info_client_pool,       
              &plot_client_pool)),          
            std::make_shared<TBinaryProtocolFactory>(),
            std::make_shared<TNonblockingServerSocket>("0.0.0.0",port),
            threadManager);
    server.setNumIOThreads(io_threads);
    std::cout << "Starting the page-service server (non blocking server) ..." << std::endl;
    server.serve();

}
