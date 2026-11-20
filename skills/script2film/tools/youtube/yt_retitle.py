"""整張播放清單批次改標題與說明（例：系列名少有人搜，在標題後面加一個比較多人搜的詞）。

  tools/youtube/.venv/bin/python tools/youtube/yt_retitle.py <播放清單 ID> --suffix "｜<後綴>" --tags-line "<#標籤 …>" --must-contain "<字串>" --out <資料夾>          # 只看，不改
  tools/youtube/.venv/bin/python tools/youtube/yt_retitle.py ... --apply   # 真的改

- 只改 snippet 的 title／description，其餘欄位（tags、categoryId、語言）原樣送回；不碰 status，所以私人排定公開不變。
- 改前把每支的 snippet＋status 存到 <資料夾>/before.json（還原用），改後重讀存 after.json，逐支比對 status 沒變。
- 已經有後綴／標籤行的片跳過（可重跑）。改一支約 50 點配額（每天 1 萬點）。
"""
import argparse, json, sys
from pathlib import Path

from googleapiclient.discovery import build

sys.path.insert(0, str(Path(__file__).parent))
from yt_upload import creds  # noqa: E402

KEEP = ("title", "description", "tags", "categoryId", "defaultLanguage", "defaultAudioLanguage")


def playlist_ids(yt, pl):
    ids, tok = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=pl, maxResults=50, pageToken=tok).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            return ids


def videos(yt, ids):
    out = []
    for i in range(0, len(ids), 50):
        out += yt.videos().list(part="snippet,status", id=",".join(ids[i:i + 50])).execute()["items"]
    return out


def main():
    ap = argparse.ArgumentParser(description="Retitle a whole playlist: append a suffix to titles and a tags line to descriptions. "
                                             "Without --apply it only shows what would change. About 50 quota points per video.")
    ap.add_argument("playlist"); ap.add_argument("--suffix", required=True); ap.add_argument("--tags-line", required=True)
    ap.add_argument("--must-contain", required=True, help="change a title only if it contains this string (guards other videos in the playlist)")
    ap.add_argument("--out", required=True); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    yt = build("youtube", "v3", credentials=creds())
    vs = videos(yt, playlist_ids(yt, a.playlist))
    if a.apply or not (out / "before.json").exists():
        (out / "before.json").write_text(json.dumps(vs, ensure_ascii=False, indent=1))
    todo = []
    for v in vs:
        s = v["snippet"]
        if a.must_contain not in s["title"]:
            print(f"· skipped (no {a.must_contain}) {v['id']} {s['title']}"); continue
        t = s["title"] if s["title"].endswith(a.suffix) else s["title"] + a.suffix
        d = s["description"] if a.tags_line in s["description"] else s["description"].rstrip() + "\n\n" + a.tags_line + "\n"
        if (t, d) == (s["title"], s["description"]):
            continue
        if len(t) > 100 or len(d.encode()) > 5000:
            sys.exit(f"✗ {v['id']} over the length limit: {t}")
        todo.append((v, t, d))
    print(f"playlist has {len(vs)} videos, {len(todo)} to change")
    for v, t, d in todo[:3] + todo[-1:]:
        print(f"  {v['id']} {v['snippet']['title']} → {t}")
    if not a.apply:
        return
    for n, (v, t, d) in enumerate(todo, 1):
        body = {k: v["snippet"][k] for k in KEEP if k in v["snippet"]}
        body.update(title=t, description=d)
        yt.videos().update(part="snippet", body={"id": v["id"], "snippet": body}).execute()
        print(f"✓ {n}/{len(todo)} {v['id']} {t}", flush=True)
    after = videos(yt, [v["id"] for v in vs])
    (out / "after.json").write_text(json.dumps(after, ensure_ascii=False, indent=1))
    b = {v["id"]: v for v in vs}
    bad = [x["id"] for x in after if x["status"] != b[x["id"]]["status"]
           or x["snippet"].get("tags") != b[x["id"]]["snippet"].get("tags")
           or x["snippet"].get("categoryId") != b[x["id"]]["snippet"].get("categoryId")]
    miss = [x["id"] for x in after if a.must_contain in x["snippet"]["title"]
            and not (x["snippet"]["title"].endswith(a.suffix) and a.tags_line in x["snippet"]["description"])]
    print(f"check: {len(bad)} with status/tags/category changed {bad}; {len(miss)} not updated {miss}")
    sys.exit(1 if bad or miss else 0)


if __name__ == "__main__":
    main()
