This repository is created in order to implement the transmission of the RGB frame stream and evaluating the distances to detected people using Raspberry Pi and Intel D435 Camera. The system works as follows: the client asks for RGB frames to process and sends back the coordinates if distances to people are needed. The received coordinates on the server side are used to calculate the distance to people that are being send to the server side.

## Install Ubuntu
Install Ubuntu for Rasperry Pi (the distrubutive may be taken from [instruction](https://ubuntu.com/download/raspberry-pi))


----

## Install Docker
Install docker following the following instruction:
1. Update and Upgrade 
sudo apt-get update && sudo apt-get upgrade
2. Download the Convenience Script and Install Docker on Raspberry Pi
```
$ curl -fsSL https://get.docker.com -o get-docker.sh
$ sudo sh get-docker.sh
```
3. Add a Non-Root User to the Docker Group
```
sudo usermod -aG docker [user_name] (Pi by default)
```
4. Logout & login
5. Check Docker Version and Info
```
docker version
docker info
```
5. Test Docker by running the Hello World Container
```
docker run hello-world
```
----

## Run docker 
Run docker using network parametres, for example:

Enter folder: modules/cam_data
```bash
$ docker build . -f Dockerfile.rp4 -t smart-space-tracking-camera
```
```bash
$ docker run —name smart-space-tracking-camera -d —privileged -v /dev:/dev -e SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR="XXX.XXX.XXX.XXX" smart-space-tracking-camera
```
- XXX.XXX.XXX.XXX is the main server address
