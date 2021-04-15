import time
import pyrealsense2 as rs
import numpy as np
import redis
import json
from turbojpeg import TurboJPEG
import os

# Cam settings
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
align = rs.align(rs.stream.color)
profile = pipeline.start(config)
depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()

# Redis
r = redis.Redis(host=os.getenv('SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR'), port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()

jpeg = TurboJPEG()

rp = int(os.getenv('IS_RP'))

last_time = 0
DM = {}


def compress_rgb(image):
    return jpeg.encode(image)


def get_frameset():
    while True:
        try:
            frameset = pipeline.wait_for_frames()
            break
        except RuntimeError:
            print('RuntimeError')
            pipeline.stop()
            pipeline.start(config)

    return frameset


def get_color_and_depth_frames():
    frameset = get_frameset()

    color_frame = frameset.get_color_frame()
    color = np.asanyarray(color_frame.get_data())

    frameset = rs.align(rs.stream.color).process(frameset)

    depth_frame = frameset.get_depth_frame()
    depth = np.asanyarray(depth_frame.get_data())

    if rp == 1:
        color = np.rot90(color, 2).astype(np.uint8)
        depth = np.rot90(depth, 2)

    # x 0.85248447 0.84908537
    # y 1.03574879 0.96441948

    return color, depth, frameset.timestamp


def send_data(msg):
    if msg['type'] != 'message':
        return

    data = json.loads(msg['data'].decode('ascii'))

    if data['req'] == 'cf':
        color_image, depth_image, timestamp = get_color_and_depth_frames()
        timestamp = '{}'.format(timestamp)
        DM[timestamp] = depth_image
        image = compress_rgb(color_image)

        pipe.set('cf_' + timestamp, image)
        pipe.publish('pipeline', json.dumps(dict(module='camera', ans='cf', ts=timestamp)))

    elif data['req'] == 'df':
        timestamp = data['ts']
        points = np.frombuffer(r.get('detect-points_' + timestamp), dtype=np.uint16)
        if points.size != 0:
            points = points.reshape((-1, 18, 2))
            distance = np.zeros(points.shape[0], dtype=np.float16)
            depth_map = DM[timestamp]

            for ind in range(distance.size):
                distance[ind] = np.mean(depth_map[points[ind][:, 0], points[ind][:, 1]]) * depth_scale

            DM.pop(timestamp)
            pipe.set('distance_' + timestamp, distance.tobytes())
        else:
            pipe.set('distance_' + timestamp, '')

        pipe.publish('pipeline', json.dumps(dict(module='camera', ans='df', ts=timestamp)))

    pipe.execute()


if __name__ == '__main__':
    for i in range(60):
        get_color_and_depth_frames()
    r.set('im-shape', '720 1280')

    p.subscribe(**{'cam-data-server': send_data})
    thread = p.run_in_thread(sleep_time=0.00001)
    thread.join()
