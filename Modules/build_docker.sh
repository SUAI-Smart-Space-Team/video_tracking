#!/bin/bash

cd show
docker build . -t smart-space-tracking-show
cd ..

cd tracker
docker build . -t smart-space-tracking-track
cd ..

cd reid
docker build . -t smart-space-tracking-reid
cd ..

cd detection
docker build . -t smart-space-tracking-detection
cd ..

cd yolact
docker build . -t smart-space-tracking-detection-yolact
cd ..

cd data_processing
docker build . -t smart-space-tracking-data-processing
cd ..

cd cam_data
docker build . -t smart-space-tracking-camera
cd ..
