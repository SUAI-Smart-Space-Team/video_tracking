import os
import struct

import redis
import numpy as np

from yolact import Yolact
from utils.augmentations import FastBaseTransform

from utils.functions import SavePath
from layers.output_utils import postprocess

from data import cfg, set_cfg

import torch
import torch.backends.cudnn as cudnn

# Detection
trained_model = 'weights/yolact_plus_resnet50_54_800000.pth'

model_path = SavePath.from_str(trained_model)
config = model_path.model_name + '_config'
set_cfg(config)

score_threshold = 0.15
top_k = 5

with torch.no_grad():
    cudnn.fastest = True
    torch.set_default_tensor_type('torch.cuda.FloatTensor')

    print('Loading model...', end='')
    net = Yolact()
    net.load_weights(trained_model)
    net.eval()
    print(' Done.')

    net = net.cuda()

    net.detect.use_fast_nms = True
    net.detect.use_cross_class_nms = False
    cfg.mask_proto_debug = False

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


def processing(dets_out, img):
    boxes = np.array([])
    masks = np.array([])

    h, w, _ = img.shape

    cfg.rescore_bbox = True
    t = postprocess(dets_out, w, h, score_threshold=score_threshold)

    idx = t[1].argsort(0, descending=True)[:top_k]

    if cfg.eval_mask_branch:
        # Masks are drawn on the GPU, so don't copy
        masks = t[3][idx]
    classes, scores, boxes = [x[idx].cpu().numpy() for x in t[:3]]

    boxes = boxes[classes == 0]
    masks = masks[classes == 0]
    scores = scores[classes == 0]
    
    boxes = boxes[scores >= 0.6]
    masks = masks[scores >= 0.6]
    scores = scores[scores >= 0.6]

    return boxes, masks.to(torch.bool).detach().cpu().numpy(), scores


def detect(msg):
    # import time
    # start = time.time()

    msg_data = msg['data'].split()
    color = fromRedis(r, msg_data[0])

    color = torch.from_numpy(color).cuda().float()
    batch = FastBaseTransform()(color.unsqueeze(0))
    preds = net(batch)

    boxes, masks, scores = processing(preds, color)

    scores = np.float64(scores)

    if len(masks.shape) > 3:
        masks = np.squeeze(masks)

    if len(masks) > 0:
        pipe.set('detect_scores', scores.tobytes())
        pipe.set('detect_boxes', boxes.tobytes())
        pipe.set('detect_masks',
                 struct.pack('>IIII', 3, masks.shape[0], masks.shape[1], masks.shape[2]) + masks.tobytes())
    else:
        pipe.set('detect_scores', np.array([]).tobytes())
        pipe.set('detect_boxes', np.array([]).tobytes())
        pipe.set('detect_masks', np.array([]).tobytes())
    pipe.execute()

    r.publish('tracker-server',
              'frame_color frame_depth frame_colorized'
              ' depth_scale'
              ' detect_scores detect_boxes detect_masks')

    # print('\rTime: {}'.format(time.time() - start), end='')


if __name__ == '__main__':
    p.subscribe(**{'detection-server': detect})
    thread = p.run_in_thread(sleep_time=0.00001)
    thread.join()
