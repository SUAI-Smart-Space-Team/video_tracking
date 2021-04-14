FROM python:3.7.10-slim

WORKDIR /server

RUN apt update && apt install -y libusb-1.0-0-dev libturbojpeg0 && rm -rf /var/lib/apt/lists/*

RUN pip install numpy redis PyTurboJPEG pyrealsense2
COPY . .
CMD ["python", "server.py"]
