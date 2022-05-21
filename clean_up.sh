#! /bin/bash

# format: <hostFile path> <cluster number> app <client IP [if it has to be cleaned]>


#common_commands="sudo docker stop \$(sudo docker ps -a -q) ; sudo docker rm \$(sudo docker ps -a -q); sudo docker system prune -f; sudo docker volume prune; sudo docker network rm social-network-overlay ;sudo kill -9 \$(pidof dockerd); sudo service docker stop "
#common_commands="sudo docker stop \$(sudo docker ps -a -q) ; sudo docker rm \$(sudo docker ps -a -q); sudo docker system prune -af; sudo docker network rm social-network-overlay ;sudo kill -9 \$(pidof dockerd); sudo service docker stop "

#don't remove images

cluster_number=1
if [ $# -gt 1 ]
then
    cluster_number=$2
fi

echo $cluster_number

declare -A appcode_mappings=( ["SN"]="social-network" ["MM"]="media-microservices" ["HR"]="hotel-reservation" ["TT"]="train-ticket" )
if [ $# -gt 2 ]
then
   app="${appcode_mappings[$3]}"
fi

common_commands="sudo docker stop \$(sudo docker ps -a -q) ; sudo docker rm \$(sudo docker ps -a -q); sudo docker volume prune -f; sudo docker network prune -f; sudo docker network rm $app-overlay-$cluster_number ;sudo kill -9 \$(pidof dockerd); sudo service docker stop "

# Reads the host file and executes the above command on all the hosts
while IFS=, read -r host yaml
do
        printf "\n\n\n\tCleaning up : $host\n\n"
	ssh -ni ~/<identity key file> ubuntu@$host "$common_commands" # -n tells ssh to read from /dev/null. Otherwise it will read the stdin(< file) completely
done < $1

# The second argument is the client VM where the load generator is running.
#if [ $# -gt 3 ]; then
#	printf "\n\n\n\tCleaning up : $3\n\n"
#	ssh -i ~/<identity key file> ubuntu@$3 "$common_commands"
#fi

consul_name="consul_"$cluster_number


sudo docker stop $consul_name
sudo docker rm $consul_name
