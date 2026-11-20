"""Beat builders for a series' make_doc.py (formats/vox-host/FORMAT.md).

Each episode used to copy these as lambdas; they now live here so every series builds beats the same way.
Output matches episode 10's make_doc.py of the author's own series key for key (tests/test_doc_format.py keeps that copy as reference).
"""

import shutil
from pathlib import Path

from doc_common import read_json

HOST_VF = "scale=1920:1080,setsar=1"


def _lines(n):
    return n if isinstance(n, list) else [n]


def ve(i, n, shot, **k):
    return {"id": i, "lines": _lines(n), "source": "ve", "shot": shot, **k}


def code(i, n, scene, params, **k):
    return {"id": i, "lines": _lines(n), "source": "code", "scene": scene, "params": params, **k}


def host(i, n, clip="host/tp_host.mp4", **k):
    """A full-frame host beat cut from the one TalkingPhoto take."""
    return {"id": i, "lines": _lines(n), "source": "clip", "clip": clip, "clip_sync": True, "vf": HOST_VF, **k}


def Q(text, by, at, size=72):
    """quote_card params."""
    return {"text": text, "by": by, "at": at, "size": size}


def tts_lines(L, fix):
    """doc["lines"] from the script lines: subtitles keep the original text, TTS gets the homophone fixes."""
    out = []
    for t in L:
        s = t
        for a, b in fix.items():
            s = s.replace(a, b)
        out.append({"text": t, **({"tts": s} if s != t else {})})
    return out


def map_route(key, crop, stops, lib=None, project=None, dim=None, push=None, **params):
    """map_route params on a map from the series map library.

    key: a map in <series>/maps/maps.json (lib: that file; default: ../maps/maps.json from the episode folder, which is
    where make_doc.py runs). crop: [x, y, w, h] on the map image, or the name of one of the map's "crops". stops: dicts
    like map_route's, where {"place": "耶利哥"} takes x / y from the map's "places" (name defaults to the place).
    The map image is copied into <episode>/refs/maps/ because doc_code only takes assets inside the episode folder.
    Unknown map, crop or place: stops with the name, so a typo never draws a dot in the wrong place."""
    P = Path(project or Path.cwd())
    lib = Path(lib or P.parent / "maps" / "maps.json")
    maps = read_json(lib)
    if key not in maps:
        raise SystemExit(f"✗ map_route: {lib} has no map \"{key}\" (it has: {', '.join(maps)})")
    m = maps[key]
    if Path(m["src"]).name != m["src"]:   # a bare file name next to maps.json: never copy from or to anywhere else
        raise SystemExit(f"✗ map_route: {key}'s src must be a file name in maps/, without a path: {m['src']}")
    if isinstance(crop, str):
        if crop not in m.get("crops", {}):
            raise SystemExit(f"✗ map_route: {key} has no crop \"{crop}\"")
        crop = m["crops"][crop]
    out = []
    for o in stops:
        o = dict(o)
        if "place" in o:
            name = o.pop("place")
            if name not in m.get("places", {}):
                raise SystemExit(f"✗ map_route: {key} has no measured place \"{name}\" (run maps/measure.py first)")
            o["x"], o["y"] = m["places"][name]
            o.setdefault("name", name)
        out.append(o)
    dst = P / "refs" / "maps" / m["src"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    src = lib.parent / m["src"]
    if not dst.exists() or dst.stat().st_size != src.stat().st_size:
        shutil.copy(src, dst)
    base = {"src": f"refs/maps/{m['src']}", "size": m["size"], "crop": list(crop), "kind": m["kind"],
            **({"credit": m["credit"]} if m.get("credit") else {}),
            **({"dim": dim} if dim is not None else {}), **({"push": push} if push is not None else {})}
    return {**params, "base": base, "stops": out}
