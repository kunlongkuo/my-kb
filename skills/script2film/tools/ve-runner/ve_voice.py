"""Re-voice finished VideoExpress clips with Voice Changer (keeps frames and length, swaps the speaker's voice).

  python3 ve_voice.py --submitted runs/<ts>/submitted.json --labels shot21_t2 shot22_t2 --ref voice.wav --out DIR
  python3 ve_voice.py --uuids <video uuid> ... --ref-id <library audio id> --out DIR

--ref uploads a local reference voice to Media Library > Audio first; --ref-id reuses one already there.
Each result is downloaded as DIR/<label or uuid>_voiced.mp4; a manifest goes to DIR/voiced.json.
Flow (probed 2026-10-09): right-click the clip in Media Library > My AI Videos > Voice Changer > Choose Sample Audio
> Audio folder > item > Choose > Apply; VE makes a new video in My AI Videos.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
from playwright.sync_api import sync_playwright

import ve_runner as v


def click_text(page, text: str, tags: str = "button"):
    page.evaluate("""([t, tags]) => { const e=[...document.querySelectorAll(tags)]
        .filter(e=>e.getBoundingClientRect().width>0&&(e.innerText||'').trim()===t).pop();
        if(!e) throw new Error('not found: '+t); e.click(); }""", [text, tags])


def voice_change(ve: v.VE, video: dict, ref_id: int, timeout: float = 600) -> dict:
    page = ve.page
    ve.open_app()
    before = {x["id"] for x in ve.library(v.VID_CAT, "", 30)}
    ve.video_menu(video, "Voice Changer")
    page.wait_for_timeout(3000)
    page.evaluate("""() => { const b=[...document.querySelectorAll('button')].find(e=>/Choose Sample Audio/.test(e.innerText)&&e.getBoundingClientRect().width>0);
                            if(!b) throw new Error('no Choose Sample Audio'); b.click(); }""")
    ve.open_folder("Audio")
    s2 = f'.library-item[data-ident="{ref_id}"]'
    page.wait_for_selector(s2, state="attached", timeout=15_000)
    page.locator(s2).first.evaluate("el => el.click()")
    page.wait_for_timeout(500)
    click_text(page, "Choose")
    page.wait_for_timeout(2000)
    click_text(page, "Apply")
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(10)
        new = [x for x in ve.library(v.VID_CAT, "", 30) if x["id"] not in before]
        if new and new[0].get("status") == "completed":
            return new[0]
        if new and "fail" in str(new[0].get("status")).lower():
            raise RuntimeError(f"Voice Changer failed: {new[0].get('status')}")
    raise RuntimeError(f"Voice Changer result not ready within {timeout / 60:.0f} min")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--submitted", help="runs/<ts>/submitted.json (with --labels)")
    src.add_argument("--uuids", nargs="+", help="video job uuids")
    ap.add_argument("--labels", nargs="+", help="labels from submitted.json")
    ref = ap.add_mutually_exclusive_group(required=True)
    ref.add_argument("--ref", help="local reference voice (wav/mp3), uploaded to Media Library > Audio")
    ref.add_argument("--ref-id", type=int, help="library id of a reference voice already in Audio")
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-dir", help="parent folder for this run's voice_<timestamp>/ folder, e.g. projects/<film>/ve-runs "
                    "(default: tools/ve-runner/runs)")
    a = ap.parse_args(argv)
    if a.submitted:
        if not a.labels:
            ap.error("--submitted needs --labels")
        sub = {x["label"]: x["video_uuid"] for x in json.loads(Path(a.submitted).read_text())}
        missing = [lb for lb in a.labels if lb not in sub]
        if missing:
            ap.error(f"labels not in {a.submitted}: {missing}")
        jobs = [(lb, sub[lb]) for lb in a.labels]
    else:
        jobs = [(u, u) for u in a.uuids]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    run_dir = v.new_run_dir(Path(a.run_dir).expanduser().resolve() if a.run_dir else v.HERE / "runs", "voice_")
    print(f"run dir: {run_dir}", flush=True)
    with sync_playwright() as pw:
        ctx = v.launch_browser(pw, v.HERE / ".profile")
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        ve = v.VE(page, run_dir, False)
        ve.open_app()
        ref_id = a.ref_id if a.ref_id else ve.upload_file(Path(a.ref).resolve(), "Audio")
        vids = {x.get("uuid"): x for x in ve.library(v.VID_CAT, "", 400)}
        manifest = {"ref_id": ref_id, "clips": {}}
        for label, uuid in jobs:
            if uuid not in vids:
                sys.exit(f"✗ {label}: video {uuid} not in the newest 400 of My AI Videos")
            res = voice_change(ve, vids[uuid], ref_id)
            dst = out / f"{label}_voiced.mp4"
            ve.download_video(res, dst)
            manifest["clips"][label] = {"source_uuid": uuid, "voiced_id": res["id"], "file": str(dst)}
            ve.log(f"{label} re-voiced as {res['id']} -> {dst}")
        (out / "voiced.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
        ctx.close()


if __name__ == "__main__":
    main()
