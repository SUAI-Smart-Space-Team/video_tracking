FROM python:3.6.12-slim-buster

WORKDIR /server

RUN apt update && apt install libusb-1.0-0
RUN pip install -r requirements.txt
RUN ["mkdir", "/a_directory"]

COPY requirements.txt requirements.txt
COPY . .

CMD ["python", "server.py"]
