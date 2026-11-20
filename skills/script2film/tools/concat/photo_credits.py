"""照片拍的當頁署名小字（用到照片的拍，在出現的當頁打一行很小的署名）。

doc.json 裡用到 assets/ 照片的程式畫面拍（photo、quote_card 的 photo、任何 params 裡的 "src": "assets/…"），
對上 assets/CREDITS.md 的「署名」欄，時間取 beats.json 那一拍。plan2concat_mcp.py --photo-credits 放進 Concat（右上角、
章節標籤下面），所以不必重渲程式畫面。同一拍用到兩張照片時署名用「；」接起來。

doc.json 有 "ai_credit"（一行字，例："AI-generated image"）時，用到生成影片的拍也在同一個位置標這行字：VE 拍、
clip 拍（主持人的 host/ 除外）、有 bg_video 的程式畫面拍；doc.json "real_footage" 列的路徑開頭是實拍，不標；"footage_credits"（路徑開頭 → 署名）的實拍改標那行署名。寫實風格的生成畫面放在新聞事件後面，觀眾可能當成真實畫面。
"""
import json
from pathlib import Path


def credit_rows(md_text):
    """CREDITS.md 表格 → {檔名: 署名}。表頭要有「檔案」與「署名」兩欄。"""
    rows, head = {}, None
    for line in md_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if head is None:
            if "檔案" in cells and "署名" in cells:
                head = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        r = dict(zip(head, cells))
        if r.get("檔案") and r.get("署名"):
            rows[r["檔案"]] = r["署名"]
    return rows


def asset_srcs(o):
    """params 裡所有 "src": "assets/<檔>" 的檔名，照出現順序、不重複。"""
    out = []
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "src" and isinstance(v, str) and v.startswith("assets/"):
                    name = v.split("/", 1)[1]
                    if name not in out:
                        out.append(name)
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(o)
    return out


def uses_generated(b, real=()):
    """這一拍的畫面有沒有用到生成影片：VE 拍、非主持人的 clip 拍、有 bg_video 的程式畫面拍。
    real：實拍影片的路徑開頭（doc.json "real_footage"，例：["footage/"]）；這些不是生成的，不標。"""
    if b.get("source") == "ve":
        return True
    src = str(b.get("clip", "")) if b.get("source") == "clip" else str((b.get("bg_video") or {}).get("src") or "")
    if not src or src.startswith("host/") or any(src.startswith(r) for r in real):
        return False
    return True


def photo_credits(doc, beats, credits):
    """[{start, dur, text}]：每個用到 assets/ 照片的程式畫面拍一段；CREDITS.md 沒有署名的照片報錯，不默默漏掉。"""
    at = {b["id"]: b for b in beats["beats"]}
    out, missing = [], []
    ai = doc.get("ai_credit")
    for b in doc["beats"]:
        names = asset_srcs(b.get("params", {})) if b.get("source") == "code" else []
        missing += [n for n in names if n not in credits]
        parts = [credits[n] for n in names if n in credits]
        fc = doc.get("footage_credits") or {}   # {"footage/wfp_": "Video: WFP"}：實拍影片的當頁署名，路徑開頭對上就標
        src = str(b.get("clip", "")) if b.get("source") == "clip" else str((b.get("bg_video") or {}).get("src") or "")
        parts += [text for prefix, text in fc.items() if src.startswith(prefix)]
        if ai and uses_generated(b, tuple(doc.get("real_footage") or ()) + tuple(fc)):
            parts.append(ai)
        text = "；".join(parts)
        if text:
            x = at[b["id"]]
            out.append({"beat": b["id"], "start": x["start"], "dur": round(x["end"] - x["start"], 3), "text": text})
    if missing:
        raise SystemExit(f"✗ assets/CREDITS.md has no credit for these photos: {', '.join(sorted(set(missing)))}")
    return out


def load(ep):
    """集資料夾 → photo_credits() 的結果。"""
    ep = Path(ep)
    return photo_credits(json.loads((ep / "doc.json").read_text(encoding="utf-8")),
                         json.loads((ep / "beats.json").read_text(encoding="utf-8")),
                         credit_rows((ep / "assets/CREDITS.md").read_text(encoding="utf-8")))


if __name__ == "__main__":
    import sys
    for r in load(sys.argv[1]):
        print(f"{r['beat']:>4} {r['start']:7.2f} +{r['dur']:5.2f}s  {r['text']}")
