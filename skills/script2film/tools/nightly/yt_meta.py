"""從 doc.json 與系列的 series.json 產 YouTube 標題與說明欄（欄位見 PromptStudio formats/vox-host/FORMAT.md §8）。

  python3 tools/nightly/yt_meta.py projects/<系列>/<NNN_xxx>/doc.json --next "<下一集的預告>"

讀封面拍（scene=cover）的 title／sub／badge 填 {book}、{chap}、{day}；series.json 的 hook_lines 指定哪幾句當開場提問。
寫出 <集>/nightly/yt_title.txt、<集>/youtube_desc.txt、<集>/nightly/yt_publish_at.txt。標題與說明都不寫「科普」。
公開時間＝series.json 的 start 起每集一天、publish_time（tz），封面的第 N 天要跟資料夾開頭 NNN 一致（用集數排，不看上傳時間）。
"""
import argparse, json, re
from datetime import date, timedelta
from pathlib import Path

from series import load as load_series


def meta(doc_path, nxt):
    """(title, desc, publish_at)；series.json 在集資料夾的上一層。"""
    P = Path(doc_path).resolve().parent
    s = load_series(P)
    doc = json.loads(Path(doc_path).read_text(encoding="utf-8"))
    cover = next(b["params"] for b in doc["beats"] if b.get("scene") == "cover")
    book, chap = cover["title"], re.sub(r"^第\s*", "", cover["sub"])          # 「第 1–11 章」→「1–11 章」
    day = re.search(r"第\s*(\d+)\s*天", cover["badge"])[1]
    assert int(day) == int(P.name.split("_")[0]), f"the cover says day {day}, which does not match the folder {P.name}"
    f = {"book": book, "chap": chap, "day": day}
    title = s["title_fmt"].format(**f)
    publish_at = f"{date.fromisoformat(s['start']) + timedelta(days=int(day) - 1)}T{s['publish_time']}:00{s['tz']}"
    hook = "\n".join(doc["lines"][n - 1]["text"] for n in s["hook_lines"])
    credit = doc["bgm"]["credit"]
    m = re.match(r"(.*?)\s*(https?://\S+)$", credit)
    body = s["desc_body"].format(hook=hook, next=nxt, credit=f"{m[1]}\n{m[2]}" if m else credit)
    desc = (s["desc_head"].format(**f) + "\n\n" + body).rstrip() + "\n"
    for bad in ("科普", "—"):
        assert bad not in title + desc, f"the title or description contains \"{bad}\""
    return title, desc, publish_at


def main():
    ap = argparse.ArgumentParser(description="YouTube title and description from doc.json and the series.json of its series.")
    ap.add_argument("doc"); ap.add_argument("--next", required=True, help="teaser text for the next episode")
    a = ap.parse_args()
    P = Path(a.doc).resolve().parent
    title, desc, publish_at = meta(a.doc, a.next)
    (P / "nightly").mkdir(exist_ok=True)
    (P / "nightly/yt_title.txt").write_text(title + "\n", encoding="utf-8")
    (P / "youtube_desc.txt").write_text(desc, encoding="utf-8")
    (P / "nightly/yt_publish_at.txt").write_text(publish_at + "\n", encoding="utf-8")
    print(title); print("public at: " + publish_at); print("---"); print(desc)


if __name__ == "__main__":
    main()
