#!/bin/bash

sh rm_started_docker.sh

docker rmi smart-space-tracking-redis
docker rmi smart-space-tracking-orca
docker rmi smart-space-tracking-postgres
docker rmi smart-space-tracking-track
docker rmi smart-space-tracking-reid
docker rmi smart-space-tracking-detection
docker rmi smart-space-tracking-data-processing
docker rmi smart-space-tracking-camera
docker rmi smart-space-tracking-show
docker rmi smart-space-tracking-pipeline
