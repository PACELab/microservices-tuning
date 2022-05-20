host_1_file=$1
host_2_file=$2
host_3_file=$3
social_network_home="~/DeathStarBench/socialNetwork"


#consul_host=130.245.168.91
consul_host=172.24.229.31
cluster_hosts=(192.168.0.226 192.168.0.228 192.168.0.229)
common_cmds="sudo dockerd -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock --cluster-advertise ens3:2375 --cluster-store consul://192.168.0.232:8500 > dockerd.log 2>&1 &"

overlay_cmd="sudo docker network create -d overlay --subnet=192.168.0.0/24 social-network-overlay"
docker_compose_template="sudo docker-compose -f filename up -d"
sudo docker run -d -p 8500:8500 -h consul --name consul progrium/consul -server -bootstrap

for host in ${cluster_hosts[*]}
do
	ssh -i ~/compass.key ubuntu@$host "$common_cmds"
done

ssh -i ~/compass.key ubuntu@$host "$overlay_cmd"

echo "${docker_compose_template/filename/$host_1_file}"

ssh -i ~/compass.key ubuntu@${cluster_hosts[0]} "cd $social_network_home;${docker_compose_template/filename/$host_1_file}"
ssh -i ~/compass.key ubuntu@${cluster_hosts[1]} "cd $social_network_home;${docker_compose_template/filename/$host_2_file}"
ssh -i ~/compass.key ubuntu@${cluster_hosts[2]} "cd $social_network_home;${docker_compose_template/filename/$host_3_file}" 

sleep 5m

ssh -i ~/compass.key ubuntu@${cluster_hosts[0]} "cd $social_network_home; python3 scripts/init_social_graph.py"


startUserId=1
endUserId=9
numReqs=200
composeRps=100
sn_home="/home/ubuntu/DeathStarBench/socialNetwork"

#$sn_home"/scripts/genPosts.py" $numReqs $composeRps $startUserId $endUserId
