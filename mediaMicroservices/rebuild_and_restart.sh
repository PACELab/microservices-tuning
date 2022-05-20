#!/bin/bash
sudo docker-compose down
sleep 3
sudo docker build --no-cache -t media-microservices -m 4g .
sudo docker-compose up -d

