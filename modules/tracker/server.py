import os
import json
import redis
from sort import *

# Tracker
mot_tracker = Sort(max_age=5, min_hits=2, iou_threshold=0.3)

# Redis
r = redis.Redis(host=os.getenv('SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR'), port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()


def track(msg):
    if msg['type'] != 'message':
        return

    data = json.loads(msg['data'].decode('ascii'))
    timestamp = data['ts']

    pipe.get('detect-scores_' + timestamp)
    pipe.get('detect-boxes_' + timestamp)
    scores, boxes = pipe.execute()

    scores = np.frombuffer(scores, dtype=np.float16)
    boxes = np.frombuffer(boxes, dtype=np.uint16)

    if boxes.size != 0:
        boxes = boxes.reshape(-1, 4)
        dots = np.hstack((boxes, scores.reshape(-1, 1)))
        track_bbs_ids = mot_tracker.update(dots).astype(np.int64)[:, -1]
        pipe.set('track_' + timestamp, track_bbs_ids.tobytes())
    else:
        mot_tracker.update()
        pipe.set('track_' + timestamp, np.array([]).tobytes())

    pipe.publish('pipeline', json.dumps(dict(module='tracker-server', ts=timestamp)))
    pipe.execute()


if __name__ == '__main__':
    p.subscribe(**{'tracker-server': track})
    thread = p.run_in_thread(sleep_time=0.00001)
    thread.join()
