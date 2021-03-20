import warnings
from collections import OrderedDict

import cv2
import torch
import torchreid
from torch import nn
from torch.nn import functional as F

import numpy as np
from default_config import get_default_config
from torchreid.utils import load_checkpoint


def load_pretrained_weights(model, weight_path):
    r"""Loads pretrianed weights to model.

    Features::
        - Incompatible layers (unmatched in name or size) will be ignored.
        - Can automatically deal with keys containing "module.".

    Args:
        model (nn.Module): network model.
        weight_path (str): path to pretrained weights.
    """
    checkpoint = load_checkpoint(weight_path)
    if 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    else:
        state_dict = checkpoint

    model_dict = model.state_dict()
    new_state_dict = OrderedDict()
    matched_layers, discarded_layers = [], []

    for k, v in state_dict.items():
        print(k)
        if k.startswith('module.base_model.'):
            k = k[len('module.base_model.'):]  # discard module.

        if k in model_dict and model_dict[k].size() == v.size():
            new_state_dict[k] = v
            matched_layers.append(k)
        else:
            discarded_layers.append(k)

    model_dict.update(new_state_dict)
    model.load_state_dict(model_dict)

    if len(matched_layers) == 0:
        warnings.warn(
            'The pretrained weights "{}" cannot be loaded, '
            'please check the key names manually '
            '(** ignored and continue **)'.format(weight_path)
        )
    else:
        print(
            'Successfully loaded pretrained weights from "{}"'.
                format(weight_path)
        )
        if len(discarded_layers) > 0:
            print(
                '** The following layers are discarded '
                'due to unmatched keys or layer size: {}'.
                    format(discarded_layers)
            )


cfg = get_default_config()
if cfg.model.old:
    model = torchreid.models.build_model(
        name=cfg.model.name,
        num_classes=cfg.model.num_classes,
        loss=cfg.model.loss,
        pretrained=cfg.model.pretrained
    )

    torchreid.utils.load_pretrained_weights(model, cfg.model.load_weights)
    model = nn.DataParallel(model).cuda()
else:
    model = torchreid.models.build_model(
        name='osnet_x0_25',
        num_classes=751,
        loss='softmax',
        pretrained=True
    )

    weight_path = 'torchreid/trained_models/3_net_E.pth'
    load_pretrained_weights(model, weight_path)
    model = nn.DataParallel(model).cuda()


@torch.no_grad()
def extract_features(input):
    """
    Extract features function
    :param input: image of type numpy array
    :return: vector of features
    """
    model.eval()
    return model(input)


def get_features_one(box_frame):
    box, frame = box_frame.values()
    frame = cv2.resize(frame, (128, 256)) / 255.
    frame = (np.rollaxis(np.array(frame), 2, 0).astype('f'))
    tensor = torch.from_numpy(frame)
    tensor = torch.nn.functional.normalize(tensor)

    img_query = np.array([tensor.numpy()])
    tensor = torch.from_numpy(img_query).cuda()

    features_img_query = F.normalize(extract_features(tensor), p=2, dim=1).cpu().numpy()

    return features_img_query[0]


def get_dist_one(query_features, gallary_features):
    distmat_arr = np.zeros(len(gallary_features))

    for i, index in enumerate(gallary_features):
        features_img_gallery = gallary_features[index]['features']
        distmat = 0
        for features in features_img_gallery:
            # difference = features - query_features
            # distmat.append(np.sqrt(difference.dot(difference)))
            distmat += np.linalg.norm(query_features - features, ord=2)
        # distmat_arr[i] = np.median(distmat)
        distmat_arr[i] = distmat / len(features_img_gallery)
    return distmat_arr
