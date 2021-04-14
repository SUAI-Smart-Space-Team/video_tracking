FROM nvidia/cuda:10.2-runtime-ubuntu18.04

WORKDIR /server

RUN apt update && apt install -y python3 python3-pip libturbojpeg  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu102/torch1.6/index.html
COPY . .

RUN python3 -c 'from DetectronAPI import DetectronAPI; DetectronAPI()'

CMD ["python3", "server.py"]
