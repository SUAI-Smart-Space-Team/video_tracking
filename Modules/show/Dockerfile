FROM python:3.6.12-slim-buster
#FROM continuumio/miniconda

WORKDIR /server
RUN apt update && apt install -y libgl1-mesa-glx libglib2.0-0 xvfb

COPY ./Modules/show/requirements.txt requirements.txt
RUN pip install -r requirements.txt

#RUN conda install -y python=3.6

#RUN conda install -y -c plotly -c anaconda -c conda-forge plotly plotly-orca flask requests numpy pillow py-opencv psutil redis-py

COPY . .
CMD ["python", "app.py"]
