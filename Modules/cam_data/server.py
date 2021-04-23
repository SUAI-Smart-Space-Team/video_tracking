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
# config.enable_device_from_file('test.bag')
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
# test
fps = 0
data_size = 0


def compress_rgb(image):
    """
    This method compesses RGB frame by TurboJPEG
    :param image: RGB frame
    :return: compressed RGB frame
    """

    return jpeg.encode(image)


def get_frameset():
    """
    This method gets frameset from  Intel Real Sense camera.
    Exceptions:
        If any errors occur during code execution,it will reconnect to Intel Real Sense camera.
        :return: set of frames
    """

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
    """
    This method stores next frameset for later processing and gets color frames. After that  it creates alignment primitive with color as its target stream and filters depth map frames
        :return: data of color frames and depth map frames
    """

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
    """
    This method sends to Redis fps parameter, color frames and  mapping between the units of the depth image and meters on request.
    Args:
        msg: request key
    """
    fps = 0
    data_size = 0

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
    fps = 1 / (time.time() - last_time)
    data_size = data_size + len(color_image) + len(depth_image)
    data_rate = data_size / (time.time() - last_time)
    testFPS(fps)
    testDataRate(data_rate)


def testFPS(fps):
    """
    This method tests fps for transmission

    """

    print('FPS =    '.format(fps))
    # toRedit(fps, 'FPS',pipe)


def testDataRate(data_rate):
    """
    This method tests data rate for transmission

    """
    print('Data rate =  '.format(data_rate))
    # toRedit(data_rate, 'DATA_RATE',pipe)

    if __name__ == '__main__':
        for i in range(60):
            get_color_and_depth_frames()
        r.set('im-shape', '720 1280')

        p.subscribe(**{'cam-data-server': send_data})
        thread = p.run_in_thread(sleep_time=0.00001)
        thread.join()
