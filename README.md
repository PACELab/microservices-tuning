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
