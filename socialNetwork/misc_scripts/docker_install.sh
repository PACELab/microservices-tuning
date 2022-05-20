apt-get update
apt install -y docker.io

service docker stop
#Change the default volume directory of the docker to a disk with lot of space
sudo mkdir docker
mv /var/lib/docker /mnt/docker
ln -s /mnt/docker /var/lib/docker

#start docker and check if installation was successful
service docker start
docker --version
