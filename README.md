# microservices-tuning
This is the code of the framework used to run the experiments of the paper titled "Reducing the Tail Latency of Microservices
Applications via Optimal Configuration Tuning" (under submission, ACSOS 2022).

## Pre-requirements
Pre-requirements for the framework and the benchmarking applications:
- Hyperopt (pip install hyperopt)
- Skopt (pip install scikit-optimize)
- Nevergrad (pip install nevergrad)
- crossplane (pip install crossplane)
- mpstat (apt-get install sysstat)
- Docker
- Docker-compose
- Python 3.5+ (with asyncio and aiohttp)
- libssl-dev (apt-get install libssl-dev)
- libz-dev (apt-get install libz-dev)
- luarocks (apt-get install luarocks)
- luasocket (luarocks install luasocket)

## How to run?
find_optimal_config.py is the script the user will run. The file argparser.py has all the details of the arguments to this file.

```
$ python3 find_optimal_config.py 
usage: find_optimal_config.py [-h] [--client CLIENT] [--rps_list RPS_LIST [RPS_LIST ...]] [--experiment_iterations EXPERIMENT_ITERATIONS] [--model_iterations MODEL_ITERATIONS] [--sequence_count SEQUENCE_COUNT]
                              [--start_sequence START_SEQUENCE] [--dimensionality_reduction DIMENSIONALITY_REDUCTION] [--acq_func ACQ_FUNC] [--warmup_duration WARMUP_DURATION] [--init] [--test]
                              [--monitoring_interval MONITORING_INTERVAL]
                              config_folder main_version {SN,MM,HR,TT} {1,2} approach
find_optimal_config.py: error: the following arguments are required: config_folder, main_version, app, cluster_number, approach
```
