FROM python:3.8.1

#WORKDIR /server

RUN apt update && apt install libusb-1.0-0 && apt install python3 && pip install pyrealsense2 && pip install redis && pip install numpy

COPY requirements.txt server.py ./

CMD ["python", "server.py"]
