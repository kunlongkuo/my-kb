"""系列設定 series.json（PromptStudio formats/vox-host/FORMAT.md §8）：放在系列資料夾（集資料夾的上一層），夜跑讀它，新系列不改腳本。

  python3 tools/nightly/series.py <集資料夾> <欄位>      印單一欄位（list 用逗號接），夜跑流程用
  python3 tools/nightly/series.py <集資料夾> playlists   主清單＋該集所屬分部清單（parts），給 yt_upload --playlist
找不到 series.json 或缺欄位：印路徑與欄位名，exit 1。
選用欄位 "font"：Concat --font 的寫法 "<family>=<路徑>"，路徑相對於系列資料夾（也可寫絕對路徑），preflight 驗那個檔在不在。
"""
import json, re, sys
from pathlib import Path

FIELDS = ("name", "title_fmt", "start", "publish_time", "tz", "playlist", "tags", "backup", "desc_head", "desc_body", "hook_lines")


def load(ep_dir):
    p = Path(ep_dir).resolve().parent / "series.json"
    if not p.exists():
        sys.exit(f"✗ series settings not found: {p}")
    s = json.loads(p.read_text(encoding="utf-8"))
    missing = [k for k in FIELDS if k not in s]
    if missing:
        sys.exit(f"✗ {p} is missing fields: {', '.join(missing)}")
    return s


USAGE = """Series settings series.json (PromptStudio formats/vox-host/FORMAT.md §8), in the series folder (one level above
the episode folder): the nightly run reads it, so a new series needs no script changes.

  python3 tools/nightly/series.py <episode folder> <field>      print one field (a list joined with commas)
  python3 tools/nightly/series.py <episode folder> playlists    main playlist plus the episode's part playlist (parts), for yt_upload --playlist
No series.json or a missing field: prints the path and field names, exit 1.
Optional field "font": written the way Concat --font takes it, "<family>=<path>", the path relative to the series folder
(or absolute); preflight checks that the file exists."""


def main():
    if len(sys.argv) != 3:
        sys.exit(USAGE)
    s = load(sys.argv[1])
    if sys.argv[2] == "playlists":   # 主清單＋集數所屬分部的清單（series.json parts；集號取集資料夾開頭的數字）
        m = re.match(r"(\d+)", Path(sys.argv[1]).resolve().name)
        ep = int(m.group(1)) if m else 0
        part = [x["playlist"] for x in s.get("parts", []) if x["from"] <= ep <= x["to"]]
        if not part:
            print(f"! episode {ep} has no part playlist (series.json parts): adding the main playlist only", file=sys.stderr)
        print(",".join([s["playlist"], *part]))
        return
    if sys.argv[2] not in s:
        sys.exit(f"✗ no field {sys.argv[2]}; fields: {', '.join(s)}")
    v = s[sys.argv[2]]
    print(",".join(map(str, v)) if isinstance(v, list) else v)


if __name__ == "__main__":
    main()
