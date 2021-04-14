import json
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import pyplot as plt

from classes import Point, Camera, Wall
from work_with_json import create_json


START_POINT = Point(0, 0, 0)
W = 5.4  # x
L = 8.8  # y
H = 2.85  # z

# angle_v -- vertical, h -- compas
camera_1 = Camera(Point(3.7, 0.84, 1.2), angle_v=90, angle_h=90)  # Направление задано углами
camera_2 = Camera(Point(2.7, 0.05, 2.80), angle_v=65, angle_h=90)  # Направление задано точкой (вектор)
cameras = [camera_1, camera_2]

# Стены задаются точками по часовой стрелке (если смотреть из комнаты) от нижней левой до нижней правой
wall_front = Wall([Point(W, 0, 0), Point(W, 0, H), Point(0, 0, H), Point(0, 0, 0)])
wall_right = Wall([Point(W, L, 0), Point(W, L, H), Point(W, 0, H), Point(W, 0, 0)])
wall_left = Wall([Point(0, 0, 0), Point(0, 0, H), Point(0, L, H), Point(0, L, 0)])
wall_back = Wall([Point(0, L, 0), Point(0, L, H), Point(W, L, H), Point(W, L, 0)])
room = [wall_front, wall_right, wall_left, wall_back]

create_json(cameras, room, 'room.json')


def show_data(room, cameras):
    fig = plt.figure()
    ax = Axes3D(fig)

    for wall in room:
        X, Y, Z = wall.make_rectangle()
        ax.plot(X, Y, Z, label='parametric curve', color='k')

    for camera in cameras:
        ax.plot(camera.point.x, camera.point.y, camera.point.z, 'ro')
        ax.plot([camera.point.x, camera.point_to.x],
                [camera.point.y, camera.point_to.y],
                [camera.point.z, camera.point_to.z], 'r--')

    ax.set_xlim3d(0, max(H, W, L))
    ax.set_ylim3d(0, max(H, W, L))
    ax.set_zlim3d(0, max(H, W, L))

    plt.show()


# show_data(room, cameras)
