FROM python:3.8.1

WORKDIR /server

RUN ["mkdir", "/a_directory"]
RUN apt update && apt install libusb-1.0-0
RUN pip install -r requirements.txt


COPY requirements.txt requirements.txt
COPY . .

CMD ["python", "server.py"]
