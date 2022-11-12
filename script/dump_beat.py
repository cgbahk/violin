from pathlib import Path
import logging
import tty
import sys
from typing import List

import hydra
from gamcho import hydra_
from just_playback import Playback
import yaml


@hydra.main(config_path=".", config_name=Path(__file__).stem)
def app(cfg):
    hydra_.make_latest_link()

    tty.setcbreak(sys.stdin)

    beats: List[float] = []

    assert Path(cfg.bgm_path).is_file()
    playback = Playback(cfg.bgm_path)
    playback.play()

    while playback.playing:
        key = sys.stdin.read(1)  # Press any key to log
        pos = playback.curr_pos

        beats.append(playback.curr_pos)
        logging.info(f"{key=}\t{pos=}")

        if key == "q":
            break

    with open("beat.yml", "w") as beat_file:
        yaml.safe_dump(beats, beat_file, sort_keys=False)


if __name__ == "__main__":
    app()
