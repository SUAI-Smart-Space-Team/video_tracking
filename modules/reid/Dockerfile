FROM nvidia/cuda:10.2-runtime-ubuntu18.04

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /server

RUN apt update && apt install -y python3 python3-pip python3-opencv cmake
RUN pip3 install scikit-build

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

CMD ["python3", "server.py"]
