import json
import uuid

import numpy as np
import redis

from Config import *
from search_coord.searching_real_coordinates import get_coordinates
from search_coord.work_with_json import read_json

r = redis.Redis(host=os.getenv('SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR'), port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()

im_shape = [int(s) for s in r.get('im-shape').split()]

room, cameras = read_json('search_coord/room.json')
camera = cameras[1]


def get_boxes_out_of_depth_frame(depth_frame, boxes, masks):
    boxes_of_frame = np.zeros(len(boxes), dtype=dict)
    for i in range(len(boxes)):
        x_left, y_top, x_right, y_bottom = boxes[i]
        depth_box = depth_frame[y_top:y_bottom, x_left:x_right]
        mask_box = masks[i][y_top:y_bottom, x_left:x_right]
        depth_box = depth_box[mask_box]
        boxes_of_frame[i] = dict(box=boxes[i], depth_box=depth_box)

    return boxes_of_frame


def clear_database():
    cursor = database_connect.cursor()
    cursor.execute('TRUNCATE tracking.track_now;')
    cursor.close()
    database_connect.commit()


def write_points_to_database(x, y, id_person):
    if id_person < 0:
        id_person = 0
    cursor = database_connect.cursor()
    cursor.execute("INSERT INTO tracking.track_now VALUES ({:f}, {:f}, '{:s}')"
                   .format(x, y, str(uuid.UUID(int=id_person))))
    cursor.close()
    database_connect.commit()


def checking_for_tables_in_db():
    cursor = database_connect.cursor()
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.schemata "
                   "WHERE  schema_name = 'tracking');")
    if not cursor.fetchone()[0]:
        cursor.execute("CREATE SCHEMA tracking;")

    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables "
                   "WHERE table_schema = 'tracking' AND table_name = 'track_now');")
    if not cursor.fetchone()[0]:
        cursor.execute("create table tracking.track_now (x real, y real, uuid uuid);")

    cursor.close()
    database_connect.commit()


def get_coord(boxes, distance, frame_shape) -> np.array:
    coordinates = []
    for ind in range(len(boxes)):
        x_left, y_top, x_right, y_bottom = boxes[ind]
        i = (x_right + x_left) // 2
        j = (y_bottom + y_top) // 2

        person_point = get_coordinates(camera=cameras[0], h=frame_shape[0], w=frame_shape[1], j=j, i=i, r=distance[ind])
        coordinates.append([person_point.y, person_point.x - 1])

    return np.array(coordinates, dtype=np.float16)


def processing(msg):
    if msg['type'] != 'message':
        return

    data = json.loads(msg['data'].decode('ascii'))
    timestamp = data['ts']

    pipe.get('detect-boxes_' + timestamp)
    pipe.get('track_' + timestamp)
    pipe.get('distance_' + timestamp)

    boxes, track_ids, distance = pipe.execute()
    boxes = np.frombuffer(boxes, dtype=np.uint16)

    if boxes.size == 0:
        clear_database()
    else:
        track_ids = np.frombuffer(track_ids, dtype=np.int64)
        boxes = boxes.reshape(-1, 4)

        if len(track_ids) == len(boxes):
            distance = np.frombuffer(distance, dtype=np.float16)
            coordinates = get_coord(boxes, distance, im_shape)
            pipe.set('coord_' + timestamp, coordinates.tobytes())

            clear_database()

            for coord, id_person in zip(coordinates, track_ids):
                x, y = coord
                if not np.isnan(x) and not np.isnan(y):
                    write_points_to_database(y, x, id_person)

    pipe.publish('pipeline', json.dumps(dict(module='data-processing-server', ts=timestamp)))
    pipe.execute()


if __name__ == '__main__':
    checking_for_tables_in_db()

    p.subscribe(**{'data-processing-server': processing})
    thread = p.run_in_thread(sleep_time=0.0005)
    thread.join()
