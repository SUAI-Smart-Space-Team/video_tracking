FROM python:3.6.12-slim-buster

#WORKDIR /server

RUN apt update && apt install libusb-1.0-0 && apt install python3 && pip install pyrealsense2 && pip install redis && pip install numpy

COPY server.py ./

CMD ["python", "server.py"]
