import os
import redis
from sort import *

# Tracker
mot_tracker = Sort(max_age=5, min_hits=2, iou_threshold=0.3)

# Redis
r = redis.Redis(host=os.getenv('SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR'), port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()


def track(msg):
    #import time
    #start = time.time()

    msg_data = msg['data'].split()

    pipe.get(msg_data[-3])
    pipe.get(msg_data[-2])
    scores, boxes = pipe.execute()
    scores = np.frombuffer(scores, dtype=np.float64)
    boxes = np.frombuffer(boxes, dtype=np.int64)
    if boxes.size != 0:
        boxes = boxes.reshape(len(boxes) // 4, 4)
        dots = np.hstack((boxes, scores.reshape(-1, 1)))

    track_bbs_ids = None
    if boxes.size == 0:
        mot_tracker.update()
    else:
        track_bbs_ids = mot_tracker.update(dots).astype(int)

    if track_bbs_ids is not None:
        pipe.set('track_bbs_ids', track_bbs_ids.tobytes())
    else:
        pipe.set('track_bbs_ids', np.array([]).tobytes())
    pipe.execute()

    r.publish('reid-server',
              'frame_color frame_depth frame_colorized '
              'depth_scale '
              'detect_scores detect_boxes detect_masks '
              'track_bbs_ids')

    #print('\rTime: {}'.format(time.time() - start), end='')


if __name__ == '__main__':
    p.subscribe(**{'tracker-server': track})
    thread = p.run_in_thread(sleep_time=0.00001)
    thread.join()
