FROM python:3.6.12-slim-buster

WORKDIR /server

COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "server.py"]
