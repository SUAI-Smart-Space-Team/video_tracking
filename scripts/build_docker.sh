#!/bin/bash

docker build ../modules/show -t smart-space-tracking-show
docker build ../modules/tracker -t smart-space-tracking-track
docker build ../modules/reid -t smart-space-tracking-reid
docker build ../modules/detection -t smart-space-tracking-detection
docker build ../modules/yolact -t smart-space-tracking-detection-yolact
docker build ../modules/data_processing -t smart-space-tracking-data-processing
docker build ../modules/cam_data -t smart-space-tracking-camera
docker build ../modules/pipeline -t smart-space-tracking-pipeline
