import numpy as np

# from classes import Point, Camera
from search_coord.classes import Camera, Point


def get_coordinates(camera: Camera, h: np.float, w: np.float,
                    j: np.float, i: np.float, r: np.float) -> Point:

    central_point_x = w / 2
    central_point_y = h / 2
    distance_to_person_point_x = np.abs(i - central_point_x)
    distance_to_person_point_y = np.abs(j - central_point_y)
    distance_to_person_point_pix = np.sqrt(distance_to_person_point_x ** 2 + distance_to_person_point_y ** 2)

    camera_vector_len = np.sqrt((camera.point.x - camera.point_to.x) ** 2 +
                                (camera.point.y - camera.point_to.y) ** 2 +
                                (camera.point.z - camera.point_to.z) ** 2)

    def point_from_ratio(point_from, point_to, ratio):
        return Point(point_from.x + (point_to.x - point_from.x) * ratio,
                     point_from.y + (point_to.y - point_from.y) * ratio,
                     point_from.z + (point_to.z - point_from.z) * ratio)

    if distance_to_person_point_pix == 0:
        return point_from_ratio(camera.point, camera.point_to, (r / camera_vector_len))
    else:
        angle_to_person_on_map = np.rad2deg(np.arccos(distance_to_person_point_x / distance_to_person_point_pix))
        angle_to_person_in_space = (camera.h / 2) * ((2 * distance_to_person_point_pix) / w)
        r_to_center_real = np.cos(np.radians(angle_to_person_in_space)) * r

        distance_to_person_point_real = np.sqrt(r ** 2 - r_to_center_real ** 2)

        central_point_real = point_from_ratio(camera.point, camera.point_to,
                                              (r_to_center_real / camera_vector_len))

        dxdy = np.sin(np.radians(angle_to_person_on_map)) * distance_to_person_point_real
        gamma = 90 - camera.angle_v if camera.angle_v <= 90 else camera.angle_v - 90
        dz = np.cos(np.radians(gamma)) * dxdy \
             * (-1 if j - central_point_y > 0 else 1) \
             * (-1 if camera.angle_v >= 90 else 1)

        dx_from_cam = np.sqrt(dxdy ** 2 - dz ** 2) \
                      * (-1 if camera.angle_v >= 90 else 1)
        dy_from_cam = distance_to_person_point_real * (90 - angle_to_person_on_map) / 90

        vector = np.array([dx_from_cam
                           * (-1 if j - central_point_y < 0 else 1),
                           dy_from_cam
                           * (-1 if i - central_point_x < 0 else 1)])

        matrix = np.array([[np.cos(np.radians(360 - camera.angle_h)),
                            -np.sin(np.radians(360 - camera.angle_h))],
                           [np.sin(np.radians(360 - camera.angle_h)),
                            np.cos(np.radians(360 - camera.angle_h))]])

        real_vector = np.dot(matrix, vector)

        return Point(central_point_real.x + real_vector[0],
                     central_point_real.y + real_vector[1],
                     central_point_real.z + dz)
