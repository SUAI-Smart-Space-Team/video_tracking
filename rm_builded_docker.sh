#!/bin/bash

docker stop smart-space-tracking-redis
docker stop smart-space-tracking-orca
docker stop smart-space-tracking-postgres
docker stop smart-space-tracking-track
docker stop smart-space-tracking-reid
docker stop smart-space-tracking-detection
docker stop smart-space-tracking-data-processing
docker stop smart-space-tracking-camera
docker stop smart-space-tracking-show

docker rm smart-space-tracking-redis
docker rm smart-space-tracking-orca
docker rm smart-space-tracking-postgres
docker rm smart-space-tracking-track
docker rm smart-space-tracking-reid
docker rm smart-space-tracking-detection
docker rm smart-space-tracking-data-processing
docker rm smart-space-tracking-camera
docker rm smart-space-tracking-show

docker rmi smart-space-tracking-redis
docker rmi smart-space-tracking-orca
docker rmi smart-space-tracking-postgres
docker rmi smart-space-tracking-track
docker rmi smart-space-tracking-reid
docker rmi smart-space-tracking-detection
docker rmi smart-space-tracking-data-processing
docker rmi smart-space-tracking-camera
docker rmi smart-space-tracking-show
