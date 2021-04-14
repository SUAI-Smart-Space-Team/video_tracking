import os
import time
import json

import redis

# Redis
r = redis.Redis(host=os.getenv('SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR'), port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()

last_time = time.time()
dict_images = {}


def processing(msg):
    if msg['type'] != 'message':
        return

    data = json.loads(msg['data'].decode('ascii'))
    timestamp = data['ts']

    if data['module'] == 'camera':
        if data['ans'] == 'cf':
            dict_images[timestamp] = {'camera-depth': False, 'detection-server': False, 'tracker-server': False,
                                      'reid-server': False}
            pipe.publish('detection-server', json.dumps(dict(module='pipeline', ts=timestamp)))
        else:
            dict_images[timestamp]['camera-depth'] = True

    elif data['module'] == 'detection-server':
        dict_images[timestamp]['detection-server'] = True
        pipe.publish('tracker-server', json.dumps(dict(module='pipeline', ts=timestamp)))
        pipe.publish('cam-data-server', json.dumps(dict(module='pipeline', req='df', ts=timestamp)))

    elif data['module'] == 'tracker-server':
        dict_images[timestamp]['tracker-server'] = True

    elif data['module'] == 'data-processing-server':
        global last_time
        pipe.set('fps', str(1 / (time.time() - last_time)))
        pipe.publish('cam-data-server', json.dumps(dict(module='pipeline', req='cf')))

        old_ts = r.get('timestamp')
        if old_ts:
            for key in r.keys(b'*' + old_ts):
                pipe.delete(key)

        pipe.set('timestamp', timestamp)
        last_time = time.time()
        pipe.execute()
        dict_images.pop(timestamp)
        return

    if dict_images[timestamp]['tracker-server'] and dict_images[timestamp]['camera-depth']:
        pipe.publish('data-processing-server', json.dumps(dict(module='pipeline', ts=timestamp)))

    pipe.execute()


if __name__ == '__main__':
    p.subscribe('pipeline')
    r.publish('cam-data-server', json.dumps(dict(module='pipeline', req='cf')))

    while True:
        message = p.get_message()
        if message:
            processing(message)
            time.sleep(0.0005)
