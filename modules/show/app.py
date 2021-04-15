from flask import Flask, render_template, Response
import io
import struct
import os

import cv2
import redis
import numpy as np
from PIL import Image
import plotly.io as pio
import plotly.graph_objects as go

from turbojpeg import TurboJPEG

# Redis
r = redis.Redis(host=os.getenv('SMART_SPACE_TRACKING_REDIS_PORT_6379_TCP_ADDR'), port=6379, db=0)
pipe = r.pipeline()
p = r.pubsub()

fig = go.Figure()
fig.update_layout(title_text="People coordinates", height=720, width=720, showlegend=False)

jpeg = TurboJPEG()

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
    fig_ylim = [0.0, 8.8]
    fig_xlim = [0, 5.4]
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
    pio.orca.config.server_url = os.getenv('SMART_SPACE_TRACKING_ORCA_PORT_9091_TCP_ADDR') + ":9091"
    pio.orca.config.use_xvfb = False
    pio.write_image(fig, buf)
    img = Image.open(buf)
    return np.array(img)



app = Flask(__name__)


def gen_frames():
    while True:
        timestamp = r.get('timestamp').decode('ascii')

        pipe.get('cf_' + timestamp)
        pipe.get('coord_' + timestamp)
        pipe.get('track_' + timestamp)
        pipe.get('fps')

        color, coordinates, track_result, fps = pipe.execute()

        if color:
            color = jpeg.decode(color)[..., ::-1]
            if coordinates and track_result:
                track_result = np.frombuffer(track_result, dtype=np.int64)
                coordinates = np.frombuffer(coordinates, dtype=np.float16).reshape(-1, 2)

                if coordinates.size != 0:
                    fig = draw_tracking(coordinates, track_result)
            else:
                fig = draw_tracking()

            im = np.hstack((color, get_im(fig)[:, :, :3]))
            ret, buffer = cv2.imencode('.jpg', cv2.resize(im[:, :, ::-1], (1800, 648)))
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            break


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
