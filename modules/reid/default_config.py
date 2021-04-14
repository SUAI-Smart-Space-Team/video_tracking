from yacs.config import CfgNode


def get_default_config():
    cfg = CfgNode()

    # reid model
    cfg.model = CfgNode()
    cfg.model.name = 'osnet_x1_0'
    cfg.model.pretrained = True  # automatically load pretrained model weights if available
    # cfg.model.load_weights = './torchreid/trained_models/osnet_x0_25_imagenet.pth' # path to model weights
    # cfg.model.load_weights = './torchreid/trained_models/osnet_x1_0_market_256x128_amsgrad_ep150_stp60_lr0.0015_b64_fb10_softmax_labelsmooth_flip.pth'  # path to model weights
    cfg.model.load_weights = './torchreid/trained_models/osnet_x1_0_msmt17_256x128_amsgrad_ep150_stp60_lr0.0015_b64_fb10_softmax_labelsmooth_flip.pth'  # path to model weights
    # cfg.model.load_weights = './torchreid/trained_models/GANOSNetGLOBAL.pth'  # path to model weights
    cfg.model.old = True
    cfg.model.num_classes = 6
    cfg.model.loss = 'softmax'
    cfg.model.threshold = 0.25
    cfg.model.refresh_threshold = 1000
    cfg.model.maxlen = 60

    return cfg
