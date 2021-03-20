import os
import time
import struct

import redis
import numpy as np
import pyrealsense2 as rs

# Cam settings
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
align = rs.align(rs.stream.color)
profile = pipeline.start(config)
depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()

# Depth filters
decimation = rs.decimation_filter()
decimation.set_option(rs.option.filter_magnitude, 3)
spatial = rs.spatial_filter()
spatial.set_option(rs.option.filter_magnitude, 2)
spatial.set_option(rs.option.filter_smooth_alpha, 1)
spatial.set_option(rs.option.filter_smooth_delta, 20)
temporal = rs.temporal_filter()
hole_filling = rs.hole_filling_filter()
depth_to_disparity = rs.disparity_transform(True)
disparity_to_depth = rs.disparity_transform(False)

# Redis
r = redis.Redis(host=os.getenv('SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR'), port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()
r.set('depth_scale', depth_scale)

last_time = 0


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
    # Store next frameset for later processing:
    frameset = get_frameset()

    color_frame = frameset.get_color_frame()
    color = np.asanyarray(color_frame.get_data())

    # Create alignment primitive with color as its target stream:
    frameset = rs.align(rs.stream.color).process(frameset)

    # Filter depth frames:
    aligned_depth_frame = frameset.get_depth_frame()
    #aligned_depth_frame = depth_to_disparity.process(aligned_depth_frame)
    #aligned_depth_frame = spatial.process(aligned_depth_frame)
    #aligned_depth_frame = temporal.process(aligned_depth_frame)
    #aligned_depth_frame = disparity_to_depth.process(aligned_depth_frame)
    #aligned_depth_frame = hole_filling.process(aligned_depth_frame)

    depth = np.asanyarray(aligned_depth_frame.get_data())

    # colorizer = rs.colorizer()
    # colorized_depth = np.asanyarray(colorizer.colorize(aligned_depth_frame).get_data())

    return color, depth, None  # colorized_depth


def fromRedis(r, name):
    encoded = r.get(name)
    if struct.unpack('>I', encoded[:4]) == 3:
        h, w, c = struct.unpack('>III', encoded[4:16])
        a = np.frombuffer(encoded[16:], dtype=np.uint8).reshape(h, w, c)
    else:
        h, w = struct.unpack('>II', encoded[4:12])
        a = np.frombuffer(encoded[12:], dtype=np.uint16).reshape(h, w)
    return a


def toRedis(arr: np.ndarray, name: str, pipe_redis):
    if len(arr.shape) == 3:
        h, w, c = arr.shape
        shape = struct.pack('>IIII', 3, h, w, c)
    else:
        h, w = arr.shape
        shape = struct.pack('>III', 2, h, w)
    encoded = shape + arr.tobytes()

    pipe_redis.set(name, encoded)
    return


def send_data(msg):
    global last_time
    pipe.set('fps', str(1 / (time.time() - last_time)))
    # print(1 / (time.time() - last_time))
    #print('FPS: {:.4f}'.format(1 / (time.time() - last_time)))
    last_time = time.time()

    # r.flushall()

    color, depth, colorized_depth = get_color_and_depth_frames()

    toRedis(color, 'frame_color', pipe)
    toRedis(depth, 'frame_depth', pipe)
    # toRedis(colorized_depth, 'frame_colorized', pipe)
    pipe.set('depth_scale', depth_scale)

    pipe.execute()

    # print('\rFPS: {}'.format(1 / (time.time() - start)), end='')

    r.publish('detection-server', 'frame_color frame_depth frame_colorized depth_scale')


if __name__ == '__main__':
    for i in range(60):
        get_color_and_depth_frames()

    p.subscribe(**{'cam-data-server': send_data})
    thread = p.run_in_thread(sleep_time=0.00001)
    send_data('test')
    thread.join()
