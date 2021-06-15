FROM python:3.7.10-slim

ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/server/pylibrs/
ENV PYTHONPATH=$PYTHONPATH:/server/pylibrs/

WORKDIR /server

RUN apt update && apt install -y libusb-1.0-0-dev libatlas-base-dev libatomic1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD ["python", "server.py"]
