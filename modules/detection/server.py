import json
import os

import redis
import numpy as np
from turbojpeg import TurboJPEG

from DetectronAPI import DetectronAPI

# Detection
detectron = DetectronAPI()

# Redis
r = redis.Redis(host=os.getenv('SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR'), port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()

jpeg = TurboJPEG()


def from_redis(rds, name):
    image = rds.get(name)
    image = jpeg.decode(image)
    return image


def get_points_from_masks(masks):
    points_list = []
    for m in masks:
        points = np.argwhere(m)
        i = len(points) // 3
        coord = np.concatenate((np.random.randint(0, i, 6),
                                np.random.randint(i, i * 2, 6),
                                np.random.randint(i * 2, i * 3, 6)))
        points = points[coord]
        points_list.append(points)

    return np.array(points_list, dtype=np.uint16)


def detect(msg):
    if msg['type'] != 'message':
        return

    data = json.loads(msg['data'].decode('ascii'))
    timestamp = data['ts']

    color_bgr = from_redis(r, 'cf_' + timestamp)

    predict = detectron.predictor(color_bgr)
    predict["instances"] = predict["instances"][predict["instances"].pred_classes == 0]
    scores = predict["instances"].scores.to('cpu').numpy().astype(np.float16)
    boxes = detectron.get_boxes(predict).astype(np.uint16)
    masks = detectron.get_masks(predict)

    points = get_points_from_masks(masks)

    pipe.set('detect-scores_' + timestamp, scores.tobytes())
    pipe.set('detect-boxes_' + timestamp, boxes.tobytes())
    pipe.set('detect-points_' + timestamp, points.tobytes())

    pipe.publish('pipeline', json.dumps(dict(module='detection-server', ts=timestamp)))
    pipe.execute()


if __name__ == '__main__':
    p.subscribe(**{'detection-server': detect})
    thread = p.run_in_thread(sleep_time=0.0005)
    thread.join()


