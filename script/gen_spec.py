from pathlib import Path
import json
import os
import random
import glob
from typing import Union, Dict, Any, List

import hydra
from gamcho import hydra_
import yaml
import omegaconf
from omegaconf import OmegaConf

RANDOM_MAGIC = "__RANDOM__"

OFFICIAL_LAYER_TYPES = [
    "title-background",
    "title",
    "subtitle",
    "news-title",
    "slide-in-text",
    "image",
    "image-overlay",
]

SAMPLE_LAYER_LISTS = [
    [{
        "type": "title-background",
        "text": "title-background",
    }],

    # Random image at center with text overlay
    [
        {
            "type": "image",
            "path": RANDOM_MAGIC,
        },
        {
            "type": "subtitle",
            "text": "Random image\nwith subtitle",
        },
    ],
    [
        {
            "type": "image",
            "path": RANDOM_MAGIC,
        },
        {
            "type": "slide-in-text",
            "text": "Random image\nwith slide-in-text",
        },
    ],
    [
        {
            "type": "image",
            "path": RANDOM_MAGIC,
        },
        {
            "type": "news-title",
            "text": "Random image\nwith news-title",
        },
    ],
    [
        {
            "type": "image",
            "path": RANDOM_MAGIC,
        },
        {
            "type": "title",
            "position": "bottom",
            "text": "Random image\nwith title",
            "zoomAmount": 0,
        },
    ],
]


def get_random_image_path(base_dir) -> str:
    assert Path(base_dir).is_dir()

    image_patterns = ("**/*.png", "**/*.jpg")

    image_paths = []
    for pattern in image_patterns:
        # Note `glob.glob` follows symlink, while `Path.glob` does not
        image_paths += glob.glob(str(Path(base_dir) / pattern), recursive=True)

    assert image_paths

    return str(random.choice(image_paths))


def compile_layer(
    orig_layer: Union[Dict[str, Any], omegaconf.DictConfig],
    *,
    cfg,  # TODO Can we remove `cfg` in argument?
) -> List[Dict[str, Any]]:
    """
    Compile single relatively high-level layer into list of raw editly-compatible layers
    """
    # Normalize type into dictionary
    orig_layer_d = None
    if isinstance(orig_layer, omegaconf.DictConfig):
        orig_layer_d = OmegaConf.to_container(orig_layer)
    if isinstance(orig_layer, dict):
        orig_layer_d = orig_layer

    assert isinstance(orig_layer_d, dict)

    # Resolve image path
    if orig_layer_d["type"] in ("image", "image-overlay") and orig_layer_d["path"] == RANDOM_MAGIC:
        orig_layer_d["path"] = get_random_image_path(cfg.random_image_base_dir)

    if orig_layer_d["type"] in OFFICIAL_LAYER_TYPES:
        return [orig_layer_d]

    if orig_layer_d["type"] == "random-layer":
        # TODO Deepcopy may make yaml dump look a bit verbose and better
        choosen_layers = random.choice(SAMPLE_LAYER_LISTS)

        ret = []
        for layer in choosen_layers:
            ret += compile_layer(layer, cfg=cfg)

        return ret

    assert False  # This means NYI


def make_spec(cfg):
    assert Path(cfg.bgm_path).is_file()
    assert Path(cfg.random_image_base_dir).is_dir()

    ret = OmegaConf.to_container(cfg.base_spec)
    ret.update(
        {
            "outPath": str(Path(os.getcwd()) / "output.mp4"),
            "audioTracks": [{
                "path": cfg.bgm_path,
                "cutFrom": cfg.start_bgm_cut_from,
            }],
        }
    )

    ret["clips"] = []
    cur_cut = cfg.start_bgm_cut_from

    for n, clip in enumerate(cfg.clips):
        layers = []
        for layer in clip.layers:
            layers += compile_layer(layer, cfg=cfg)

        ret["clips"].append(
            {
                "duration": clip.bgm_cut_to - cur_cut,  # TODO This may accumulate error
                "layers": layers,
            }
        )

        cur_cut = clip.bgm_cut_to

    return ret


@hydra.main(config_path=".", config_name=Path(__file__).stem)
def app(cfg):
    hydra_.make_latest_link()

    spec = make_spec(cfg)

    with open("spec.yml", "w") as yml_file:
        yaml.dump(spec, yml_file)

    with open("spec.json", "w") as json_file:
        json.dump(spec, json_file, indent=2)


if __name__ == "__main__":
    app()
