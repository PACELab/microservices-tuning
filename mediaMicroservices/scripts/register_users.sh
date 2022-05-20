#!/usr/bin/env bash

hostName=$1
hostPort=$2
for i in {1..1000}; do
  curl -d "first_name=first_name_"$i"&last_name=last_name_"$i"&username=username_"$i"&password=password_"$i \
      http://$hostName:$hostPort/wrk2-api/user/register
done
