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
find_optimal_config.py is the script the user will run.

```
$ python3 find_optimal_config.py -h
usage: find_optimal_config.py [-h] [--client CLIENT] [--rps_list RPS_LIST [RPS_LIST ...]] [--experiment_iterations EXPERIMENT_ITERATIONS] [--model_iterations MODEL_ITERATIONS] [--sequence_count SEQUENCE_COUNT]
                              [--start_sequence START_SEQUENCE] [--dimensionality_reduction DIMENSIONALITY_REDUCTION] [--acq_func ACQ_FUNC] [--warmup_duration WARMUP_DURATION] [--init] [--test]
                              [--monitoring_interval MONITORING_INTERVAL]
                              config_folder main_version {SN,MM,HR,TT} {1,2} approach

positional arguments:
  config_folder         The folder where the details of the application are present
  main_version          The name for this round of experiments
  {SN,MM,HR,TT}         The application being used
  {1,2}                 The cluster on which the experiments are to be run.
  approach              The optimization algorithm to be used

optional arguments:
  -h, --help            show this help message and exit
  --client CLIENT       The IP of the client machine
  --rps_list RPS_LIST [RPS_LIST ...], -r RPS_LIST [RPS_LIST ...], -R RPS_LIST [RPS_LIST ...]
                        The rps list at which experiments are to be run
  --experiment_iterations EXPERIMENT_ITERATIONS, -ei EXPERIMENT_ITERATIONS
                        The number of times the experiment is repeated for a given algorithm and config (0th iteration is run for cache warm-up
  --model_iterations MODEL_ITERATIONS, -mi MODEL_ITERATIONS
                        The number of iterations the algorithm is run in each sequence
  --sequence_count SEQUENCE_COUNT, -sc SEQUENCE_COUNT
                        The number of times the algorithm is rerun
  --start_sequence START_SEQUENCE, -ss START_SEQUENCE
                        Starting sequence number
  --dimensionality_reduction DIMENSIONALITY_REDUCTION, -d DIMENSIONALITY_REDUCTION
                        The dimensionality reduction method used
  --acq_func ACQ_FUNC, -a ACQ_FUNC
                        The acquisition function to be used with Bayesian methods
  --warmup_duration WARMUP_DURATION, -wd WARMUP_DURATION
                        The duration of the warump in minutes
  --init                Initialize the algorithm with user supplied points instead of library generated random samples.
  --test                Temporary flags that is used to test a feature conditionally.
  --monitoring_interval MONITORING_INTERVAL
                        The interval at which the config is changed
```

To run 50 iterations of Bayesian optimization (with Gaussian Process as the surrogate) for the social networking (SN) application without any dimensionality reduction, the arguments would be:

```
find_optimal_config.py -nsdi-50iters-500 SN 1 bayesopt-gp --rps_list 500 --dimensionality_reduction all -mi 50 -sc=1
```
