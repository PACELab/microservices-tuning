#! /bin/bash
cluster_hosts=(serverless-9 serverless-10 serverless-11 serverless-12)

echo ${cluster_hosts[0]}
#set of common commands to be executed across all the hosts
common_commands="sudo docker stop \$(sudo docker ps -a -q) ; sudo docker rm \$(sudo docker ps -a -q); sudo docker system prune -fa; sudo kill -9 \$(pidof dockerd); sudo service docker stop "

for host in ${cluster_hosts[*]}
do
	printf "\n\n\n\tCleaning up : $host\n\n"
	ssh -i ~/compass.key ubuntu@$host "$common_commands"
done
#delete overlay network
#ssh -i compass.key ubuntu@$host_1 "sudo docker network rm social-network-overlay"

ssh -i compass.key ubuntu@$host_1 "sudo docker network rm hotelreservation-overlay"

sudo docker stop consul
sudo docker rm consul
