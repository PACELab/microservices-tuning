#!/usr/bin/env bash
hostName=$1
hostPort=$2
for i in {1..1000}; do
  curl -d "title=title_"$i"&movie_id=movie_id_"$i \
      http://$hostName:$hostPort/wrk2-api/movie/register
done
