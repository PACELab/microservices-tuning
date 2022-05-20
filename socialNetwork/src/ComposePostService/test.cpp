#include <iostream>
#include <fstream>
#include <string.h>

using namespace std;

main()
{
  int io_threads = -1;
  int worker_threads = -1;

  // Change the io_thread and worker_thread number based on the configuration selected
  string ms_prefix = "compose-post";
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
  cout << io_threads << " " << worker_threads ;
}
