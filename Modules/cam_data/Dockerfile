FROM python:3.8.1

#WORKDIR /server

RUN apt update && apt install libusb-1.0-0 && apt install python3

COPY requirements.txt server.py ./

RUN pip install -r requirements.txt


#COPY requirements.txt requirements.txt


CMD ["python", "server.py"]
