"""ve_collect.py — download finished AI videos from the VideoExpress media library.

ve_runner.py submits shots and records their job uuids; rendering finishes minutes
later. This lists "My AI Videos" through the library API, waits until the wanted
items are completed, and downloads them via library/download/<id>, using the same
logged-in profile as ve_runner.

  python3 ve_collect.py --since 2026-10-08T16:48:00Z --out DIR            # every AI video since then
  python3 ve_collect.py --since ... --map shots.json --out DIR             # name files shotN.mp4

--submitted: runs/<ts>/submitted.json written by ve_runner.py — exact match by job uuid (preferred).
--map: JSON {"shot1": "2026-10-08T16:49:14Z", ...} — submission times (UTC); each
shot gets the library item created closest after its time (within 120 s). Legacy runs only.
"""
import argparse, json, sys, time
from datetime import datetime, timedelta
from pathlib import Path
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
APP = "https://app.videoexpress.ai/"
LIST = APP + "api/library/get_media/4?categoryId={cat}&page=1&start=0&limit={limit}&query=&orderBy=id&orderDir=desc&filter="

def ts(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", help="UTC ISO time; ignore older items (default: earliest submission)")
    ap.add_argument("--submitted", help="ve_runner runs/<ts>/submitted.json: match clips by job uuid")
    ap.add_argument("--out", required=True)
    ap.add_argument("--map", help="JSON file: {name: submit time UTC}")
    ap.add_argument("--category", default="557393", help="'My AI Videos' folder id")
    ap.add_argument("--wait", type=int, default=30, help="minutes to wait for processing items")
    ap.add_argument("--limit", type=int, default=400,
                    help="newest N library items to search, 1-1000 (same default as ve_voice.py)")
    a = ap.parse_args()
    a.limit = max(1, min(a.limit, 1000))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    by_uuid = {x["label"]: x["video_uuid"] for x in json.loads(Path(a.submitted).read_text())} if a.submitted else None
    if not a.since and not by_uuid:
        ap.error("--since is required without --submitted")
    since = ts(a.since) if a.since else min(ts(x["submitted_utc"]) for x in json.loads(Path(a.submitted).read_text())) \
        - timedelta(minutes=1)
    want = {k: ts(v) for k, v in json.loads(Path(a.map).read_text()).items()} if a.map else None

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(str(HERE / ".profile"), channel="chrome", headless=True)
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        pg.goto(APP)
        deadline = time.time() + a.wait * 60
        while True:
            try:
                res = pg.request.get(LIST.format(cat=a.category, limit=a.limit), timeout=60_000).json()["results"]
            except Exception as e:  # noqa: BLE001  transient "socket hang up": poll again
                print(f"[{time.strftime('%H:%M:%S')}] list failed ({str(e).splitlines()[0][:80]}), retrying", flush=True)
                if time.time() > deadline:
                    raise
                time.sleep(15)
                continue
            items = [x for x in res if ts(x["datetime"]) >= since]
            if by_uuid:
                pick = {name: next((x for x in items if x.get("uuid") == u), None) for name, u in by_uuid.items()}
            elif want:
                pick = {}
                for name, t in want.items():
                    c = sorted((x for x in items if 0 <= (ts(x["datetime"]) - t).total_seconds() <= 120),
                               key=lambda x: ts(x["datetime"]))
                    pick[name] = c[0] if c else None
            else:
                pick = {f"{x['id']}": x for x in items}
            missing = [n for n, x in pick.items() if x is None]
            pending = [n for n, x in pick.items() if x and x["status"] != "completed"]
            print(f"[{time.strftime('%H:%M:%S')}] {len(pick)} wanted, {len(pending)} processing, {len(missing)} not found", flush=True)
            if not pending or time.time() > deadline:
                break
            time.sleep(30)
        manifest = {}
        for name, x in pick.items():
            if not x or x["status"] != "completed":
                manifest[name] = {"status": x["status"] if x else "not found"}
                continue
            dst = out / f"{name}.mp4"
            r = pg.request.get(APP + f"library/download/{x['id']}", timeout=120_000)
            body = r.body()
            if r.status != 200 or body[4:8] != b"ftyp":
                manifest[name] = {"status": f"download failed {r.status}", "id": x["id"]}
                continue
            dst.write_bytes(body)
            manifest[name] = {"id": x["id"], "uuid": x.get("uuid"), "file": dst.name, "created": x["datetime"],
                              "duration_s": round(x["duration"] / 1000, 3), "first_frame": x["imagePath"]}
            print(f"  {name}: {dst.name} {len(body)//1024} KB", flush=True)
        (out / "collect.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
        ctx.close()
    bad = [n for n, m in manifest.items() if "file" not in m]
    sys.exit(f"not downloaded: {bad}" if bad else 0)

if __name__ == "__main__":
    main()
