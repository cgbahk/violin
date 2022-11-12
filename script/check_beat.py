from pathlib import Path
import os
import json

import hydra
from gamcho import hydra_
import yaml


def make_spec(cfg):
    assert Path(cfg.bgm_path).is_file()
    assert Path(cfg.beat_path).is_file()

    with open(cfg.beat_path) as beat_file:
        beats = yaml.safe_load(beat_file)

    ret = {}
    ret.update(
        {
            "width": 640,
            "height": 480,
            "outPath": str(Path(os.getcwd()) / "output.mp4"),
            "audioTracks": [{
                "path": cfg.bgm_path,
                "cutFrom": beats[0],
            }],
            "defaults": {
                "transition": None,
            }
        }
    )

    ret["clips"] = []
    cur_cut = beats[0]

    for beat_time in beats[1:]:
        ret["clips"].append(
            {
                "duration": beat_time - cur_cut,  # TODO This may accumulate error
                "layers":
                [{
                    "type": "title-background",
                    "text": f"{cur_cut:.2f} ~ {beat_time:.2f}",
                }],
            }
        )

        cur_cut = beat_time

    ret["clips"].append({
        "duration": 5,
        "layers": [{
            "type": "title-background",
            "text": "Fin."
        }],
    })

    return ret


@hydra.main(config_path=".", config_name=Path(__file__).stem)
def app(cfg):
    hydra_.make_latest_link()

    spec = make_spec(cfg)

    with open("spec.yml", "w") as yml_file:
        yaml.safe_dump(spec, yml_file, sort_keys=False)

    with open("spec.json", "w") as json_file:
        json.dump(spec, json_file)


if __name__ == "__main__":
    app()
