./docker_compose_install.sh
./docker_install.sh
./other_reqs.sh
git clone https://github.com/delimitrou/DeathStarBench.git
cd DeathStarBench/socialNetwork/
docker-compose up -d
python3 scripts/init_social_graph.py
