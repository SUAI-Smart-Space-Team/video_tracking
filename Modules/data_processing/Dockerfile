FROM python:3.6.12-slim-buster

ENV DB_NAME=postgres
ENV DB_USER=postgres
ENV DB_PASSWORD=iotlab96
ENV DB_PORT=5432

WORKDIR /server

RUN apt update && apt install -y python3-psycopg2

COPY ./Modules/data_processing/requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "server.py"]
