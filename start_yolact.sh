#!/bin/bash

sh rm_started_docker.sh

docker run --name smart-space-tracking-redis -d -p 6379:6379 redis
docker run --name smart-space-tracking-orca -d -p 9091:9091 quay.io/plotly/orca
docker run -d --name smart-space-tracking-postgres -e POSTGRES_PASSWORD=iotlab96 -p 5432:5432 -d postgres

docker run -d --name smart-space-tracking-track --link smart-space-tracking-redis smart-space-tracking-track

docker run --gpus all -d --name smart-space-tracking-reid --link smart-space-tracking-redis smart-space-tracking-reid

docker run --gpus all -d --name smart-space-tracking-detection --link smart-space-tracking-redis smart-space-tracking-detection-yolact

docker run -d --name smart-space-tracking-data-processing --link smart-space-tracking-redis --link smart-space-tracking-postgres smart-space-tracking-data-processing

sleep 40

docker run --name smart-space-tracking-camera -d --privileged --link smart-space-tracking-redis -v /dev:/dev smart-space-tracking-camera

docker run -p 5555:5000 -d --name smart-space-tracking-show --link smart-space-tracking-redis --link smart-space-tracking-orca smart-space-tracking-show

echo ""
echo "Open http://localhost:5555"
echo "If you see the video from the camera, then everything works"

