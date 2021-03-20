import os
import struct
import collections

import redis
import numpy as np
from default_config import get_default_config
from utils import get_features_one, get_dist_one

# ReID
cfg_reid = get_default_config()
body_bank_test = {}

# Redis
r = redis.Redis(host=os.getenv('SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR'), port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()


def reid(color_boxes_of_frame, track_bbs_ids_for_reid):
    track_ids_for_reid = [int(b[-1]) for b in track_bbs_ids_for_reid]

    result_arr_id = np.array([-1] * len(color_boxes_of_frame)).astype(np.int32)

    if len(body_bank_test) == 0:
        for index in range(len(color_boxes_of_frame)):
            # extract features
            features_img_query = get_features_one(color_boxes_of_frame[index])
            deque = collections.deque(maxlen=cfg_reid.model.maxlen)
            deque.append(features_img_query)
            # save features and distance
            body_bank_test[track_ids_for_reid[index]] = {'id': len(body_bank_test) + 1, 'features': deque}

            result_arr_id[index] = len(body_bank_test)
    else:
        if len(color_boxes_of_frame) != 0:
            used_numbers = {k: False for k in body_bank_test.keys()}

            for index in range(len(color_boxes_of_frame)):
                body_bank_keys = list(body_bank_test.keys())
                track_id = track_ids_for_reid[index]

                if track_id in body_bank_keys:
                    if len(body_bank_test[track_id]['features']) == cfg_reid.model.maxlen:
                        for x in range(cfg_reid.model.maxlen // 2):
                            body_bank_test[track_id]['features'].pop()
                    features = get_features_one(color_boxes_of_frame[index])
                    body_bank_test[track_id]['features'].append(features)

                    result_arr_id[index] = body_bank_test[track_id]['id']
                    used_numbers[track_id] = True
                else:
                    features = get_features_one(color_boxes_of_frame[index])
                    dist_mat_arr = get_dist_one(features, body_bank_test).astype(np.float32)
                    # print(dist_mat_arr)
                    dist_mat_arr[list(used_numbers.values())] = 10_000_000
                    # print(dist_mat_arr)
                    # print()

                    min_index = np.argmin(dist_mat_arr, axis=None)
                    min_dist = dist_mat_arr[min_index]

                    if min_dist > cfg_reid.model.threshold:
                        deque = collections.deque(maxlen=cfg_reid.model.maxlen)
                        deque.append(features)
                        body_bank_test[track_id] = {'id': len(body_bank_test) + 1, 'features': deque}
                        result_arr_id[index] = len(body_bank_test)
                        used_numbers[track_id] = True
                    else:
                        key = body_bank_keys[min_index]
                        body_bank_test[key]['features'].append(features)
                        body_bank_test[track_id] = body_bank_test.pop(key)
                        result_arr_id[index] = body_bank_test[track_id]['id']

                        used_numbers[track_id] = True
                        used_numbers.pop(key)

    return np.array(result_arr_id)


def get_boxes_out_of_color_frame(color_frame, boxes, masks):
    boxes_of_frame = np.zeros(len(boxes), dtype=dict)
    for i in range(len(boxes)):
        x_left, y_top, x_right, y_bottom = boxes[i]
        color_box = color_frame[y_top:y_bottom, x_left:x_right]
        mask_box = masks[i][y_top:y_bottom, x_left:x_right]
        color_box = np.where(np.dstack((mask_box, mask_box, mask_box)), color_box, 0)
        boxes_of_frame[i] = dict(box=[x_left, y_top, x_right, y_bottom], color_box=color_box)

    return boxes_of_frame


def fromRedis(r, name):
    encoded = r.get(name)
    if struct.unpack('>I', encoded[:4])[0] == 3:
        h, w, c = struct.unpack('>III', encoded[4:16])
        a = np.frombuffer(encoded[16:], dtype=np.uint8).reshape(h, w, c)
    else:
        h, w = struct.unpack('>II', encoded[4:12])
        a = np.frombuffer(encoded[12:], dtype=np.uint16).reshape(h, w)
    return a


def reid_processing(msg):
    #import time
    #start = time.time()

    msg_data = msg['data'].split()

    pipe.get(msg_data[0])
    pipe.get(msg_data[-3])
    pipe.get(msg_data[-2])
    pipe.get(msg_data[-1])

    color, boxes, masks, track_bbs_ids = pipe.execute()
    boxes = np.frombuffer(boxes, dtype=np.int64)
    # np.uint8 np.int64 np.bool np.int64
    
    reid_result = np.frombuffer(track_bbs_ids, dtype=np.int64).astype(np.int32)
    if reid_result.size != 0:
        reid_result = list(reid_result.reshape(len(reid_result) // 5, 5))
        reid_result = [int(b[-1]) for b in reid_result]
        reid_result = np.array(reid_result, dtype=np.int32)

    #reid_result = np.array([])
    if False and boxes.size != 0:
        boxes = boxes.reshape(len(boxes) // 4, 4)
        track_bbs_ids = np.frombuffer(track_bbs_ids, dtype=np.int64)
        if track_bbs_ids.size != 0:
            track_bbs_ids = list(track_bbs_ids.reshape(len(track_bbs_ids) // 5, 5))

        if len(track_bbs_ids) == len(boxes):
            color = np.frombuffer(color[16:], dtype=np.uint8).reshape(struct.unpack('>III', color[4:16]))[:, :, ::-1]
            masks = np.frombuffer(masks[16:], dtype=np.bool).reshape(struct.unpack('>III', masks[4:16]))

            reid_result = reid(get_boxes_out_of_color_frame(color, boxes, masks), track_bbs_ids)

    r.set('reid_result', reid_result.tobytes())

    r.publish('data-processing-server',
              'frame_color frame_depth frame_colorized '
              'depth_scale '
              'detect_scores detect_boxes detect_masks '
              'track_bbs_ids '
              'reid_result')

    #print('\rTime: {}'.format(time.time() - start), end='')


if __name__ == '__main__':
    p.subscribe(**{'reid-server': reid_processing})
    thread = p.run_in_thread(sleep_time=0.00001)
    thread.join()
