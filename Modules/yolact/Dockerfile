FROM nvidia/cuda:10.2-cudnn8-devel-ubuntu18.04

RUN apt update && apt install -y python3 python3-pip

RUN pip3 install cython redis
RUN pip3 install install torch==1.4.0 torchvision==0.5.0

WORKDIR /server
COPY . .

WORKDIR /server/external/DCNv2
RUN python3 setup.py build develop
WORKDIR /server

RUN pip3 install --upgrade pip
RUN pip3 install scikit-build
RUN pip3 install opencv-python
RUN apt-get install ffmpeg libsm6 libxext6 git  -y
RUN pip3 install git+https://github.com/haotian-liu/cocoapi.git#"egg=pycocotools&subdirectory=PythonAPI"

CMD ["python3", "server.py"]
