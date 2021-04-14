# Установка с нуля

## Установка nvidia-docker и его проверка

Сначала установите драйвера [nvidia!](https://linuxconfig.org/how-to-install-the-nvidia-drivers-on-ubuntu-20-04-focal-fossa-linux)

```bash
$ curl https://get.docker.com | sh && sudo systemctl --now enable docker
$ sudo groupadd docker
$ sudo gpasswd -a $USER docker
```
Log out/in to activate the changes to groups.

Install nvidia docker

```bash
$ distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
    && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
    && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
```

```bash
$ sudo apt-get update
$ sudo apt-get install -y nvidia-docker2
```

```bash
$ sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.orig
$ sudo cp daemon.json /etc/docker/daemon.json
$ sudo systemctl restart docker
```

```bash
$ docker run --rm --gpus all nvidia/cuda:10.2-runtime-ubuntu18.04 nvidia-smi
```

This should result in a console output shown below:

```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 450.51.06    Driver Version: 450.51.06    CUDA Version: 11.0     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                               |                      |               MIG M. |
|===============================+======================+======================|
|   0  Tesla T4            On   | 00000000:00:1E.0 Off |                    0 |
| N/A   34C    P8     9W /  70W |      0MiB / 15109MiB |      0%      Default |
|                               |                      |                  N/A |
+-------------------------------+----------------------+----------------------+

+-----------------------------------------------------------------------------+
| Processes:                                                                  |
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |
|        ID   ID                                                   Usage      |
|=============================================================================|
|  No running processes found                                                 |
+-----------------------------------------------------------------------------+
```

## Build modules

```bash
$ cd modules
$ sh build_docker.sh
$ sh start_docker.sh
```

## Start
```bash
$ go to main folder (cd ..)
$ sh start.sh
```
