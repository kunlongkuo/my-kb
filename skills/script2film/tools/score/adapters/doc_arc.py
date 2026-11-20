"""doc 模式的片（doc.json＋beats.json）→ 分段配樂：一段一個風格，接成一條 wav。整支一個風格聽起來太平、像沒有配樂，
所以照故事的起伏換風格（例：前段 story 收斂 → 轉折那一拍切 scifi 鼓組 → 收尾回 story）。
只讀 doc.json 與 beats.json；產物寫在工作資料夾（預設 <專案>/score/，見 paths.py）。

用法：uv run python adapters/doc_arc.py <專案>/doc.json [--name <名>] [--out <wav>] [--work <資料夾>] [--render]
doc.json "bgm"：
  "arc": [{"from": 拍, "style": story|scifi|devotion|lounge|bazaar, "gain": LU（預設 0；起伏大的那段給 +2）}]，第一段的 from 要是第一拍；
         沒寫 arc＝整支一段 story
  "roles": {拍: 角色}  覆寫自動判的角色（角色只能用 ROLES 那八個）
沒覆寫的拍照畫面判角色（SCENE_ROLE）；bgm.drops 的拍＝pause；第一拍 intro、最後一拍 outro。
hits：slam 的數字卡／比較卡（stat_count、compare 的 "slam"）在砸下來那一刻（at 的字＋0.12 秒）打一下。
--render：每段 score.py make → check_align（要 PASS）→ 量響度、各段拉到 BASE_LUFS＋gain → 接起來：
  進到 scifi 段硬切（前段 0.3 秒淡出、後段 0.03 秒淡入，靠 hit 蓋住接縫），其他接縫前段 1.5 秒淡出、後段 1 秒淡入。
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[3] / "tools/config"))
import s2f_config; s2f_config.load()
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SC))
from paths import work_dir  # noqa: E402

ROLES = ("intro", "title", "verse", "body", "warm", "reflect", "pause", "outro")
SCENE_ROLE = {"cover": "intro", "stat_count": "title", "burst_title": "title", "compare": "verse", "timeline": "body",
              "bars": "body", "list_reveal": "body", "map_route": "body", "web_evidence": "body", "screen_step": "body",
              "photo": "warm", "quote_card": "reflect", "object_draw": "reflect", "credits": "outro"}
SOURCE_ROLE = {"ve": "body", "clip": "verse", "host": "verse"}
HARD_IN = ("scifi",)
BASE_LUFS = -30.0   # 各段先拉齊再接；doc_cut 會把整條再壓到 doc.json bgm.lufs
SLAM_DELAY = 0.12   # lib.js slamIn：落地時間


class ArcError(ValueError):
    pass


def role_of(beat, doc):
    over = doc.get("bgm", {}).get("roles", {})
    if beat["id"] in over:
        if over[beat["id"]] not in ROLES:
            raise ArcError(f"bgm.roles {beat['id']}: the role must be one of {', '.join(ROLES)}")
        return over[beat["id"]]
    if beat["id"] in doc.get("bgm", {}).get("drops", []):
        return "pause"
    return SCENE_ROLE.get(beat.get("scene"), SOURCE_ROLE.get(beat.get("source"), "verse"))


def phrase_at(beat, phrase):
    """Seconds from the beat's start where phrase opens in its tokens (punctuation and spaces ignored), or None."""
    words = [t[0] for t in beat.get("tokens", [])]
    q = [c for c in re.sub(r"[\s，。、？！,.?!：:；;「」『』（）()]", "", str(phrase))]
    joined = "".join(words)
    i = joined.find("".join(q)) if q else -1
    if i < 0:
        return None
    k = n = 0
    while n + len(words[k]) <= i:   # token index holding character i
        n += len(words[k]); k += 1
    return beat["tokens"][k][1]


def hits(doc_beats, beats):
    by_id, out = {b["id"]: b for b in beats}, []
    for d in doc_beats:
        p, b = d.get("params", {}), by_id.get(d["id"])
        if not (b and p.get("slam")):
            continue
        if d.get("scene") == "stat_count" and isinstance(p.get("at"), str):
            t = phrase_at(b, p["at"])
            if t is not None:
                out.append((b["start"] + t + SLAM_DELAY, f"{d['id']} slam"))
        elif d.get("scene") == "compare":
            for side in ("left", "right"):
                at = p.get(side, {}).get("at")
                t = phrase_at(b, at) if isinstance(at, str) else None
                if t is not None:
                    out.append((b["start"] + t + 0.25 + SLAM_DELAY, f"{d['id']} {side} slam"))
    return sorted(out)


def build_parts(doc, beats, name):
    """→ [events dict]，一段一個；時間是該段自己的秒數。"""
    if not beats:
        raise ArcError("beats.json has no beats")
    doc_by_id = {d["id"]: d for d in doc["beats"]}
    total = beats[-1]["start"] + beats[-1]["duration"]
    arc = doc.get("bgm", {}).get("arc") or [{"from": beats[0]["id"], "style": "story"}]
    ids = [b["id"] for b in beats]
    if arc[0]["from"] != ids[0]:
        raise ArcError(f"bgm.arc: the first part must start at the first beat {ids[0]}")
    for a in arc:
        if a["from"] not in ids:
            raise ArcError(f"bgm.arc: no beat {a['from']}")
    starts = [beats[ids.index(a["from"])]["start"] for a in arc] + [total]
    if starts != sorted(starts):
        raise ArcError("bgm.arc must follow the film's order")
    all_hits = hits(doc["beats"], beats)
    parts = []
    for k, a in enumerate(arc):
        t0, t1 = starts[k], starts[k + 1]
        secs = []
        for b in beats:
            if t0 - 0.01 <= b["start"] < t1 - 0.01:
                role = role_of({**doc_by_id.get(b["id"], {}), **b}, doc)
                if b["id"] == ids[0]:
                    role = "intro"
                elif b["id"] == ids[-1]:
                    role = "outro"
                if not secs or secs[-1]["role"] != role:   # 同角色的連續拍併成一段
                    secs.append({"t": round(b["start"] - t0, 2), "role": role, "label": b["id"]})
        parts.append({"name": f"{name}-p{k + 1}", "duration": round(t1 - t0, 2), "style": a.get("style", "story"),
                      "under_voice": True, "motif": "auto", "sections": secs,
                      "hits": [{"t": round(t - t0, 2), "label": lab} for t, lab in all_hits if t0 + 0.3 <= t < t1 - 0.3],
                      "_gain": float(a.get("gain", 0))})
    return parts


def run(cmd):
    r = subprocess.run(cmd, cwd=SC, capture_output=True, text=True)
    if r.returncode:
        raise ArcError(f"{' '.join(map(str, cmd))} failed:\n{r.stdout[-800:]}{r.stderr[-800:]}")
    return r.stdout


def lufs(wav):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])


def render(parts, out, work):
    inputs, chain = [], []
    (work / "events").mkdir(parents=True, exist_ok=True)
    for k, p in enumerate(parts):
        ev = work / "events" / f"{p['name']}.json"
        ev.write_text(json.dumps({x: v for x, v in p.items() if not x.startswith("_")}, ensure_ascii=False, indent=1), encoding="utf-8")
        run(["uv", "run", "python", "score.py", "--work", str(work), "make", str(ev)])
        wav, plan = work / "outputs" / f"{p['name']}.wav", work / "plans" / f"{p['name']}.json"
        print(f"{p['name']} ({p['style']}) {run(['uv', 'run', 'python', 'check_align.py', str(wav), str(plan)]).strip().splitlines()[-1]}")
        gain = BASE_LUFS + p["_gain"] - lufs(wav)
        nxt = parts[k + 1]["style"] if k + 1 < len(parts) else None
        fo = 0.3 if nxt in HARD_IN else 1.5
        fi = 0.03 if p["style"] in HARD_IN else 1.0
        f = f"[{k}]volume={gain:.2f}dB"
        if k:
            f += f",afade=t=in:d={fi}"
        if nxt:
            f += f",afade=t=out:st={p['duration'] - fo:.3f}:d={fo}"
        chain.append(f + f"[a{k}]")
        inputs += ["-i", str(wav)]
    fc = ";".join(chain) + ";" + "".join(f"[a{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1,alimiter=limit=0.89[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[o]", "-ar", "48000", str(out)], check=True)
    print(f"→ {out} ({sum(p['duration'] for p in parts):.2f}s, {len(parts)} parts)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc")
    ap.add_argument("--name")
    ap.add_argument("--out")
    ap.add_argument("--work", help="work folder for events/, plans/, outputs/ (default: $S2F_SCORE_WORK, else <episode>/score)")
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    doc_path = Path(a.doc).resolve()
    doc = json.loads(doc_path.read_text(encoding="utf-8"))
    beats = json.loads((doc_path.parent / "beats.json").read_text(encoding="utf-8"))["beats"]
    name = a.name or f"doc-{doc_path.parent.name}"
    try:
        parts = build_parts(doc, beats, name)
        for p in parts:
            print(f"{p['name']} {p['style']} {p['duration']}s: " + " ".join(f"{s['label']}={s['role']}" for s in p["sections"])
                  + (f" | hits {', '.join(h['label'] for h in p['hits'])}" if p["hits"] else ""))
        if a.render:
            work = work_dir(a.work, doc_path.parent / "score")
            work.mkdir(parents=True, exist_ok=True)
            render(parts, Path(a.out).resolve() if a.out else work / f"{name}.wav", work)
    except ArcError as e:
        sys.exit(f"✗ {e}")


if __name__ == "__main__":
    main()
