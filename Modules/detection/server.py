import os
import struct

import redis
import numpy as np
from DetectronAPI import DetectronAPI

# Detection
detectron = DetectronAPI()

# Redis
r = redis.Redis(host=os.getenv('SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR'), port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()


def fromRedis(r, name):
    encoded = r.get(name)
    if struct.unpack('>I', encoded[:4])[0] == 3:
        h, w, c = struct.unpack('>III', encoded[4:16])
        a = np.frombuffer(encoded[16:], dtype=np.uint8).reshape(h, w, c)
    else:
        h, w = struct.unpack('>II', encoded[4:12])
        a = np.frombuffer(encoded[12:], dtype=np.uint16).reshape(h, w)
    return a


def detect(msg):
    #import time
    #start = time.time()

    msg_data = msg['data'].split()
    color = fromRedis(r, msg_data[0])

    predict = detectron.predictor(color)
    predict["instances"] = predict["instances"][predict["instances"].pred_classes == 0]
    scores = predict["instances"].scores.to('cpu').numpy().astype('float')
    boxes = detectron.get_boxes(predict)
    masks = detectron.get_masks(predict)

    if len(masks) > 0:
        pipe.set('detect_scores', scores.tobytes())
        pipe.set('detect_boxes', boxes.tobytes())
        pipe.set('detect_masks', struct.pack('>IIII', 3, masks.shape[0], masks.shape[1], masks.shape[2]) + masks.tobytes())
    else:
        pipe.set('detect_scores', np.array([]).tobytes())
        pipe.set('detect_boxes', np.array([]).tobytes())
        pipe.set('detect_masks', np.array([]).tobytes())
    pipe.execute()

    r.publish('tracker-server',
              'frame_color frame_depth frame_colorized'
              ' depth_scale'
              ' detect_scores detect_boxes detect_masks')

    #print('\rTime: {}'.format(time.time() - start), end='')


if __name__ == '__main__':
    p.subscribe(**{'detection-server': detect})
    thread = p.run_in_thread(sleep_time=0.00001)
    thread.join()
