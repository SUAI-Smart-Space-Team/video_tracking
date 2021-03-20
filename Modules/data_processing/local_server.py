import io
import uuid
import struct

#import cv2
import redis
import numpy as np
#from PIL import Image
#import plotly.io as pio
#import plotly.graph_objects as go

from Config import *

# Redis
r = redis.Redis(host='127.0.0.1', port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()

#fig = go.Figure()
#fig.update_layout(title_text="People coordinates", height=720, width=720, showlegend=False)


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


def get_coordinates(boxes_depth_frame, width):
    coordinates = []
    for box in boxes_depth_frame:
        x_left, y_top, x_right, y_bottom = box['box']
        distance = np.mean(np.mean(box['depth_box']))
        dist_sin_ang = distance * np.sin(np.deg2rad(camera_angle))
        # dist_sin_ang = np.sqrt(np.abs(distance * distance - 2.7 * 2.7)) * np.sin(np.deg2rad(camera_angle))
        # dist_sin_ang = distance

        angle_alpha = 90 / width * (np.mean((x_right, x_left)) - width // 2)
        x = np.cos(np.deg2rad(angle_alpha)) * dist_sin_ang
        y = np.sin(np.deg2rad(angle_alpha)) * dist_sin_ang

        coordinates.append([x, y])
    return np.array(coordinates, dtype=np.float)


def draw_tracking(coords=None, ids=None):
    if coords is None:
        figure = go.Figure()
    else:
        # Fig for the coordinates of a person's location
        figure = go.Figure(data=[
            go.Scatter(
                x=coords[::, 1],
                y=coords[::, 0],
                mode='markers',
                marker=dict(size=25, color=list(ids))
            )
        ])
    figure.update_xaxes(range=fig_xlim)
    figure.update_yaxes(range=fig_ylim)
    figure.update_layout(title_text="People coordinates", height=720, width=720, showlegend=False)

    return figure


def get_im(fig):
    buf = io.BytesIO()
    pio.orca.config.server_url = "http://localhost:9091"
    pio.orca.config.use_xvfb = False
    pio.write_image(fig, buf)
    img = Image.open(buf)
    return np.array(img)


def processing(msg):
    msg_data = msg['data'].split()

    pipe.get(msg_data[0])
    pipe.get(msg_data[1])
    pipe.get(msg_data[-4])
    pipe.get(msg_data[-3])
    pipe.get(msg_data[-2])
    pipe.get(msg_data[-1])
    pipe.get(msg_data[3])

    color, depth, boxes, masks, track_bbs_ids, reid_result, depth_scale = pipe.execute()
    boxes = np.frombuffer(boxes, dtype=np.int64)
    # color = np.frombuffer(color[16:], dtype=np.uint8).reshape(struct.unpack('>III', color[4:16]))[:, :, ::-1]

    global fig
    pipe.delete('coordinates')
    if boxes.size == 0:
        clear_database()
        #fig = draw_tracking()
        # vis.plotlyplot(fig, win='Plot')
    else:
        track_bbs_ids = np.frombuffer(track_bbs_ids, dtype=np.int64)
        if track_bbs_ids.size != 0:
            track_bbs_ids = list(track_bbs_ids.reshape(len(track_bbs_ids) // 5, 5))

        boxes = boxes.reshape(len(boxes) // 4, 4)

        if len(track_bbs_ids) == len(boxes):
            depth = np.frombuffer(depth[12:], dtype=np.uint16).reshape(struct.unpack('>II', depth[4:12]))
            masks = np.frombuffer(masks[16:], dtype=np.bool).reshape(struct.unpack('>III', masks[4:16]))
            reid_result = np.frombuffer(reid_result, dtype=np.int32)

            depth = depth * float(depth_scale)

            boxes_depth_frame = get_boxes_out_of_depth_frame(depth, boxes, masks)
            coordinates = get_coordinates(boxes_depth_frame, depth.shape[1])
            pipe.set('coordinates', coordinates.tostring())

            clear_database()
            #fig = draw_tracking(coordinates, reid_result)

            for coord, id_person in zip(coordinates, reid_result):
                x, y = coord
                if not np.isnan(x) and not np.isnan(y):
                    write_points_to_database(y, x, id_person)

    pipe.execute()

    # print(coordinates)
    #im = np.hstack((color, get_im(fig)[:, :, :3]))
    #cv2.imshow('frame', im[:, :, ::-1])
    #if cv2.waitKey(1) & 0xFF == ord('q'):
    #    return

    # print('\rTime: {}'.format(time.time() - start), end='')

    r.publish('cam-data-server', 'done')


if __name__ == '__main__':
    checking_for_tables_in_db()
    p.subscribe(**{'data-processing-server': processing})
    thread = p.run_in_thread(sleep_time=0.00001)
    thread.join()
