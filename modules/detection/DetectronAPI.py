import numpy as np

from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg


class DetectronAPI:
    def __init__(self):
        # Detectron2 configs
        self.cfg = get_cfg()
        self.cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
        self.cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")

        # self.cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_1x.yaml"))
        # self.cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_50_FPN_1x.yaml")

        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
        self.predictor = DefaultPredictor(self.cfg)

        print('Init')

    def predictor(self, img):
        print('Start predict')
        return self.predictor(img)

    @staticmethod
    def get_boxes(outputs):
        return outputs["instances"].pred_boxes.to('cpu').tensor.numpy().astype('int')

    @staticmethod
    def get_masks(outputs):
        return outputs["instances"].pred_masks.to('cpu').numpy()

    @staticmethod
    def get_boxes_out_of_color_frame(color_frame, boxes, masks):
        boxes_of_frame = np.zeros(len(boxes), dtype=dict)
        for i in range(len(boxes)):
            x_left, y_top, x_right, y_bottom = boxes[i]
            color_box = color_frame[y_top:y_bottom, x_left:x_right]
            mask_box = masks[i][y_top:y_bottom, x_left:x_right]
            color_box = np.where(np.dstack((mask_box, mask_box, mask_box)), color_box, 0)
            boxes_of_frame[i] = dict(box=[x_left, y_top, x_right, y_bottom], color_box=color_box)

        return boxes_of_frame

    # @staticmethod
    # def get_boxes_out_of_color_frame(color_frame, boxes):
    #     boxes_of_frame = np.zeros(len(boxes), dtype=dict)
    #     for i in range(len(boxes)):
    #         x_left, y_top, x_right, y_bottom = boxes[i]
    #         color_box = color_frame[y_top:y_bottom, x_left:x_right]
    #         boxes_of_frame[i] = dict(box=[x_left, y_top, x_right, y_bottom], color_box=color_box)
    #
    #     return boxes_of_frame

    @staticmethod
    def get_boxes_out_of_depth_frame(depth_frame, boxes, masks):
        boxes_of_frame = np.zeros(len(boxes), dtype=dict)
        for i in range(len(boxes)):
            x_left, y_top, x_right, y_bottom = boxes[i]
            depth_box = depth_frame[y_top:y_bottom, x_left:x_right]
            mask_box = masks[i][y_top:y_bottom, x_left:x_right]
            depth_box = depth_box[mask_box]
            boxes_of_frame[i] = dict(box=boxes[i], depth_box=depth_box)

        return boxes_of_frame

    # @staticmethod
    # def get_boxes_out_of_depth_frame(depth_frame, boxes):
    #     boxes_of_frame = np.zeros(len(boxes), dtype=dict)
    #     for i in range(len(boxes)):
    #         x_left, y_top, x_right, y_bottom = boxes[i]
    #         depth_box = depth_frame[y_top:y_bottom, x_left:x_right]
    #         boxes_of_frame[i] = dict(box=boxes[i], depth_box=depth_box)
    #
    #     return boxes_of_frame
