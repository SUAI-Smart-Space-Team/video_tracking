FROM python:3.7.10-slim

WORKDIR /server
RUN apt update && apt install -y libgl1-mesa-glx libglib2.0-0 xvfb libturbojpeg0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "app.py"]
