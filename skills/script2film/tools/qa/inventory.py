"""素材盤點（formats/vox-host/FORMAT.md §6 第 7 點）：送 VE 之前量三個數，只印不擋。

  python3 tools/qa/inventory.py <集資料夾> [--sec-per-char 0.21]

  1 連續只有程式畫面（純字卡）的最長秒數，從哪一拍到哪一拍
  2 每支背景影片（bg_video）累計用了幾秒
  3 照片／VE／字卡的比例；主持人另列，不佔這三欄

有 beats.json 用對時後的實測長度，沒有就照字數估（每字秒數含句間停頓，預設 0.21）。
分類：clip／ve 拍是 VE（clip 在 host/ 底下的是主持人）；photo 場景放了 assets/ 底下的照片是照片；影片原色全畫面
（bg_video 的 tone 是 full）算 VE；右框或圓框有主持人的字卡另列一類；其餘是字卡（把影片調淡當底的也算字卡）。
結果另寫 <集>/nightly/inventory.json。
"""
import argparse, collections, json
from pathlib import Path

HOST, VE, PHOTO, CARD, CARD_HOST = "host", "VE", "photo", "card", "card + host frame"


def durations(doc, real, k):
    """{拍: 秒}。beats.json 有的用實測；沒有的照這一拍的字數估，同一句切成幾拍時照 from 的位置分。"""
    lines, out = [l["text"] for l in doc["lines"]], {}
    for b in doc["beats"]:
        if b["id"] in real:
            out[b["id"]] = real[b["id"]]
            continue
        t = "".join(lines[n - 1] for n in b["lines"])
        s = len(t) * k
        sib = [x for x in doc["beats"] if x["lines"] == b["lines"]]
        if len(sib) > 1 and t and sib[1].get("from") and sib[1]["from"] in t:
            cut = t.find(sib[1]["from"]) / len(t)
            s *= cut if b is sib[0] else (1 - cut) / (len(sib) - 1)
        elif len(sib) > 1:   # 切點找不到：平分，不讓同一句被算好幾次
            s /= len(sib)
        out[b["id"]] = s
    return out


def kind(doc, b):
    if b.get("source") in ("clip", "ve"):
        return HOST if str(b.get("clip", "")).startswith("host/") else VE
    photos = (b.get("params") or {}).get("photos") or []
    if b.get("scene") == "photo" and photos and str(photos[0].get("src", "")).startswith("assets/"):
        return PHOTO
    if (b.get("bg_video") or {}).get("tone") == "full":
        return VE
    framed = (doc.get("side") or {}).get("beats", []) + (doc.get("pip") or {}).get("beats", [])
    return CARD_HOST if b["id"] in framed else CARD


def inventory(doc, real=None, k=0.21):
    real = real or {}
    dur = durations(doc, real, k)
    tot, bg = collections.Counter(), collections.Counter()
    run, best, start, span = 0.0, 0.0, None, [None, None]
    for b in doc["beats"]:
        d, kd = dur[b["id"]], kind(doc, b)
        tot[kd] += d
        if b.get("bg_video"):
            bg["/".join(Path(b["bg_video"]["src"]).parts[-2:])] += d
        if kd == CARD:
            start = b["id"] if run == 0 else start
            run += d
            if run > best:
                best, span = run, [start, b["id"]]
        else:
            run = 0.0
    total = sum(tot.values())
    body = total - tot[HOST]
    share = {key: (tot[name] / body if body else 0.0) for key, name in
             (("photo", PHOTO), ("ve", VE), ("card", CARD), ("card_host", CARD_HOST))}
    share["host"] = tot[HOST] / total if total else 0.0
    return {"measured": bool(real), "total": round(total, 1),
            "card_run_max": {"sec": round(best, 1), "from": span[0], "to": span[1]},
            "bg_video": {name: round(v, 1) for name, v in bg.most_common()},
            "share": {name: round(v, 4) for name, v in share.items()}}


def summary(inv):
    s, c = inv["share"], inv["card_run_max"]
    top = next(iter(inv["bg_video"].items()), None)
    return (f"{'measured' if inv['measured'] else 'estimated'} {inv['total']:.0f}s; longest run of plain cards {c['sec']:.0f}s"
            + (f" ({c['from']}–{c['to']})" if c["from"] else "")
            + (f"; most on one background video {top[1]:.0f}s ({top[0]})" if top else "; no background video")
            + f"; without the host: photo {s['photo']:.0%}, VE {s['ve']:.0%}, card {s['card']:.0%}, card + host frame {s['card_host']:.0%}; host {s['host']:.0%} of the film")


def over_targets(inv, targets):
    """系列設定的目標（checklist.targets：photo／ve 是 [下限, 上限]，card_max 是上限）：回傳超出的說明，只是標記。"""
    s, out = inv["share"], []
    for key, name in (("photo", "photo"), ("ve", "VE")):
        if key in targets and not targets[key][0] <= s[key] <= targets[key][1]:
            out.append(f"{name} {s[key]:.0%} outside the target {targets[key][0]:.0%}–{targets[key][1]:.0%}")
    if "card_max" in targets and s["card"] + s["card_host"] > targets["card_max"]:
        out.append(f"card {s['card'] + s['card_host']:.0%} above the target {targets['card_max']:.0%}")
    return out


def run(ep, k=0.21, write=True):
    ep = Path(ep)
    doc = json.loads((ep / "doc.json").read_text(encoding="utf-8"))
    bj = ep / "beats.json"
    real = {b["id"]: b["end"] - b["start"] for b in json.loads(bj.read_text(encoding="utf-8"))["beats"]} if bj.exists() else {}
    inv = inventory(doc, real, k)
    if write:
        (ep / "nightly").mkdir(exist_ok=True)
        (ep / "nightly/inventory.json").write_text(json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8")
    return inv


def main():
    ap = argparse.ArgumentParser(description="Inventory (formats/vox-host/FORMAT.md §6 point 7): three numbers measured before sending to VE, printed, never blocking.")
    ap.add_argument("episode")
    ap.add_argument("--sec-per-char", type=float, default=0.21)
    a = ap.parse_args()
    inv = run(a.episode, a.sec_per_char)
    print(summary(inv))
    print("background video totals:", ", ".join(f"{n} {v:.0f}s" for n, v in inv["bg_video"].items()) or "none")


if __name__ == "__main__":
    main()
