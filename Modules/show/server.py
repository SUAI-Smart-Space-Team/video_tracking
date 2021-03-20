import io
import time
import struct

import cv2
import redis
import numpy as np
from PIL import Image
import plotly.io as pio
import plotly.graph_objects as go

# Redis
r = redis.Redis(host='127.0.0.1', port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()

fig = go.Figure()
fig.update_layout(title_text="People coordinates", height=720, width=720, showlegend=False)


def get_boxes_out_of_depth_frame(depth_frame, boxes, masks):
    boxes_of_frame = np.zeros(len(boxes), dtype=dict)
    for i in range(len(boxes)):
        x_left, y_top, x_right, y_bottom = boxes[i]
        depth_box = depth_frame[y_top:y_bottom, x_left:x_right]
        mask_box = masks[i][y_top:y_bottom, x_left:x_right]
        depth_box = depth_box[mask_box]
        boxes_of_frame[i] = dict(box=boxes[i], depth_box=depth_box)

    return boxes_of_frame


def draw_tracking(coords=None, ids=None):
    fig_ylim = [0.0, 11.0]
    fig_xlim = [-4, 4]
    if coords is None:
        figure = go.Figure()
    else:
        # Fig for the coordinates of a person's location
        figure = go.Figure(data=[
            go.Scatter(
                x=coords[::, 1],
                y=coords[::, 0],
                mode='markers',
                marker=dict(size=20, color=list(ids))
            )
        ])
    figure.update_xaxes(range=fig_xlim)
    figure.update_yaxes(range=fig_ylim)
    figure.update_layout(title_text="People coordinates", height=720, width=720, showlegend=False)

    return figure


def get_im(fig):
    buf = io.BytesIO()
    pio.orca.config.server_url = "0.0.0.0:9091"
    pio.orca.config.use_xvfb = False
    pio.write_image(fig, buf)
    img = Image.open(buf)
    return np.array(img)


def processing():
    start = time.time()

    pipe.get('frame_color')
    pipe.get('coordinates')
    pipe.get('reid_result')
    pipe.get('fps')

    color, coordinates, reid_result, fps = pipe.execute()

    if color:
        color = np.frombuffer(color[16:], dtype=np.uint8).reshape(struct.unpack('>III', color[4:16]))[:, :, ::-1]
        if coordinates and reid_result:
            reid_result = np.frombuffer(reid_result, dtype=np.int32)
            coordinates = np.frombuffer(coordinates, dtype=np.float).reshape(-1, 2)

            if coordinates.size != 0:
                fig = draw_tracking(coordinates, reid_result % 10)
        else:
            fig = draw_tracking()

        # im = color
        im = np.hstack((color, get_im(fig)[:, :, :3]))
        cv2.imshow('frame', cv2.resize(im[:, :, ::-1], (1800, 648)))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return

    if fps:
        print('\rFPS | SYSTEM: {:.4} | SHOW: {:.2f}'.format(fps.decode('ascii'), 1 / (time.time() - start)), end='')


if __name__ == '__main__':
    while True:
        processing()
