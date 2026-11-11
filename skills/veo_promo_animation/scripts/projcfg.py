"""讀 project.json：所有路徑都相對於 root。"""
import json
from pathlib import Path

DEFAULTS = {
    "work_dir": "Codex/anim_work",
    "scenes_py": "Codex/anim/scenes.py",
    "voice_timing": "Codex/anim/voice_timing.json",
    "voice_dir": "Codex/配音/audio",
    "veo_dir": "Codex/video/veo",
    "parts_dir": "Codex/video/parts",
    "output": "Codex/video/宣傳動畫_完整版.mp4",
    "xfade": 0.3,          # 鏡與鏡在金色光帶下的溶接秒數
    "tail": 0.2,           # 前一鏡光帶最亮後再留的秒數
    "credits_xfade": 1.0,
    "bgm_volume": 0.30,
    "loudness": -15,
    "bgm_join": {"a_end": 62.0, "crossfade": 4.0},
}


class Cfg(dict):
    def path(self, key):
        v = self[key]
        p = Path(v)
        return p if p.is_absolute() else Path(self["root"]) / p

    def scene(self, sid):
        for s in self["scenes"]:
            if s["id"] == sid:
                return s
        raise SystemExit(f"project.json 沒有場景 {sid}")


def load(path):
    d = json.load(open(path, encoding="utf-8"))
    c = Cfg({**DEFAULTS, **d})
    c["root"] = str(Path(c.get("root") or Path(path).resolve().parent))
    return c
