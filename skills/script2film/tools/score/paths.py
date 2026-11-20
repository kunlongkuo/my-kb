"""Where the composer reads its SoundFont and writes what it makes.

Work folder (events/, plans/, outputs/ are made under it): --work, else $S2F_SCORE_WORK, else the caller's default
(adapters/doc_arc.py: <episode>/score next to doc.json; score.py and compose.py: ./score_out where the command is run).
Nothing an episode produces is written next to these programs.

SoundFont: $S2F_SOUNDFONT, else $S2F_ASSETS_LOCAL/soundfonts/GeneralUser-GS.sf2. It is not shipped with the repo
(32 MB; its licence allows use in music and in software, but its author cannot vouch for the origin of every sample:
NOTICE.md), so a missing file stops with where to get it.
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import os
import sys
from pathlib import Path

SF2_NAME = "GeneralUser-GS.sf2"
SF2_URL = "https://github.com/mrbumpy409/GeneralUser-GS"


def work_dir(arg=None, default=None):
    return Path(arg or os.environ.get("S2F_SCORE_WORK") or default or Path.cwd() / "score_out").expanduser().resolve()


def soundfont():
    tried = []
    if os.environ.get("S2F_SOUNDFONT"):
        tried.append(Path(os.environ["S2F_SOUNDFONT"]).expanduser())
    elif os.environ.get("S2F_ASSETS_LOCAL"):
        tried.append(Path(os.environ["S2F_ASSETS_LOCAL"]).expanduser() / "soundfonts" / SF2_NAME)
    for p in tried:
        if p.is_file():
            return p
    sys.exit(f"✗ SoundFont not found ({', '.join(map(str, tried)) or 'neither S2F_SOUNDFONT nor S2F_ASSETS_LOCAL is set'}): "
             f"download {SF2_NAME} from {SF2_URL} and put it in $S2F_ASSETS_LOCAL/soundfonts/, or set S2F_SOUNDFONT to the file")
