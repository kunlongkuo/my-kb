#!/usr/bin/env python3
"""VideoExpress「First Frame, Last Frame」跑單：每段的首格與末格都由我們指定，影片在兩格之間生成。

一般生成的 8 秒對打常在 4–5 秒後停成站樁；首末格模式會收在指定的末格，但一次試片
中段有慢動作感，觀感不如一般生成接末格。要的是「準確收在某個姿勢」時才用它。
上一段的末格直接當下一段的首格（first: "chain"），不必等影片生完。

跑單（JSON）：
{
  "aspect": "16:9",                 # 或 "9:16"（VE 說直式效果較好）
  "takes": 2,                       # 每段用同一組首末格送幾支影片
  "suffix": "Real-time speed ...",  # 接在每段 video 提示詞後面（可省略）
  "shots": [
    {"id": "K1", "dur": 8, "first": 46248150,   # My AI Images 的圖片 id
     "last": "Smart Edit 提示詞：從首格改出末格", "video": "兩格之間發生什麼"},
    {"id": "K2", "dur": 8, "first": "chain", "last": "...", "video": "..."}   # chain＝上一段存下的末格
  ]
}

用法：python3 ve_frames.py sheet.json [--run-dir DIR] [--shots K2 K3] [--first-id 123]
挑末格：和 ve_runner 一樣，ve_qc.py <run> 等關卡、ve_qc.py <run> 1|r|s 回答。
收片：python3 ve_collect.py --submitted <run>/submitted.json --out <dir>
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

DESCRIPTION = """VideoExpress "First Frame, Last Frame" run sheet: we set the first and last frame of each segment,
and the video is generated between them.

Plain generation of an 8 s fight often settles into standing still after 4-5 s; first/last frame mode ends on the
given last frame, but in one trial the middle felt slow-motion and looked worse than plain generation ending on a
last frame. Use it only when the shot must land exactly on a pose.
A segment's last frame is used directly as the next segment's first frame (first: "chain"), without waiting for the video.

Run sheet (JSON):
{
  "aspect": "16:9",                 # or "9:16" (VE says portrait works better)
  "takes": 2,                       # videos sent per segment with the same first/last frames
  "suffix": "Real-time speed ...",  # appended to each segment's video prompt (optional)
  "shots": [
    {"id": "K1", "dur": 8, "first": 46248150,   # image id in My AI Images
     "last": "Smart Edit prompt: turn the first frame into the last", "video": "what happens between the frames"},
    {"id": "K2", "dur": 8, "first": "chain", "last": "...", "video": "..."}   # chain = last frame saved by the previous segment
  ]
}

usage: python3 ve_frames.py sheet.json [--run-dir DIR] [--shots K2 K3] [--first-id 123]
Pick last frames as with ve_runner: ve_qc.py <run> waits for the gate, ve_qc.py <run> 1|r|s answers.
Collect: python3 ve_collect.py --submitted <run>/submitted.json --out <dir>
"""

ROOT_JS = """() => { const t=document.querySelector('#opt_video_prompt'); let r=t;
  for(let i=0;i<14&&r.parentElement;i++) r=r.parentElement; return r; }"""


class SheetError(ValueError):
    pass


def load_sheet(d: dict) -> dict:
    """檢查跑單、補預設值；錯了丟 SheetError（訊息含欄位）。"""
    if d.get("aspect", "16:9") not in ("16:9", "9:16"):
        raise SheetError("aspect: must be 16:9 or 9:16")
    takes = d.get("takes", 1)
    if not (isinstance(takes, int) and 1 <= takes <= 5):
        raise SheetError("takes: an integer from 1 to 5")
    shots = d.get("shots")
    if not (isinstance(shots, list) and shots):
        raise SheetError("shots: at least one segment")
    ids = set()
    for i, s in enumerate(shots):
        where = f"shots[{i}]"
        if not s.get("id") or s["id"] in ids:
            raise SheetError(f"{where}.id: required and unique")
        ids.add(s["id"])
        if not (isinstance(s.get("dur"), int) and 3 <= s["dur"] <= 10):
            raise SheetError(f"{where}.dur: an integer from 3 to 10 seconds (VE's first/last frame range)")
        first = s.get("first")
        if first == "chain":
            if i == 0:
                raise SheetError(f"{where}.first: the first segment cannot chain to a previous one")
        elif not isinstance(first, int):
            raise SheetError(f"{where}.first: an image id (integer) or \"chain\"")
        for k in ("last", "video"):
            if not (isinstance(s.get(k), str) and s[k].strip()):
                raise SheetError(f"{where}.{k}: required text")
    return {"aspect": d.get("aspect", "16:9"), "takes": takes, "suffix": d.get("suffix", "").strip(), "shots": shots}


def video_prompt(sheet: dict, shot: dict) -> str:
    return " ".join(x for x in (shot["video"].strip(), sheet["suffix"]) if x)


def main():
    ap = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sheet")
    ap.add_argument("--run-dir", help="parent folder for this run (suggested: projects/<film>/ve-runs)")
    ap.add_argument("--shots", nargs="*", help="run only these ids; if the first one is chain, give --first-id")
    ap.add_argument("--first-id", type=int, help="when the first segment to run is chain, use this image as its first frame")
    a = ap.parse_args()
    try:
        sheet = load_sheet(json.loads(Path(a.sheet).read_text(encoding="utf-8")))
    except SheetError as e:
        sys.exit(f"✗ run sheet error: {e}")
    todo = [s for s in sheet["shots"] if not a.shots or s["id"] in a.shots]
    if todo and todo[0]["first"] == "chain" and not a.first_id:
        sys.exit(f"✗ {todo[0]['id']} chains to the previous segment's last frame, but that segment is not in this run: give the first-frame image id with --first-id")

    from playwright.sync_api import sync_playwright

    import ve_runner as R

    run_dir = R.new_run_dir(Path(a.run_dir).expanduser().resolve() if a.run_dir else R.HERE / "runs", "frames_")
    print(f"run dir: {run_dir}")
    with sync_playwright() as pw:
        ctx = R.launch_browser(pw, R.HERE / ".profile")
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        ve = R.VE(page, run_dir, False)
        ve.open_app()
        ve.dismiss_news()
        fr = Frames(ve, R, sheet["aspect"])
        fr.open_modal(sheet["aspect"])
        submitted, saved, prev_last = [], {}, a.first_id
        for shot in todo:
            first = prev_last if shot["first"] == "chain" else shot["first"]
            if first is None:
                ve.log(f"{shot['id']} skipped: it chains from a shot that was skipped")
                continue
            fr.set_first(first)
            src = fr.make_last(shot["id"], shot["last"])
            if src is None:
                ve.log(f"{shot['id']} skipped at QC (no video); the next chain shot has no first frame")
                prev_last = None
                continue
            prev_last = fr.save_last(src)
            saved[shot["id"]] = prev_last
            (run_dir / "saved.json").write_text(json.dumps(saved, indent=1))
            fr.set_duration(shot["dur"])
            vp = video_prompt(sheet, shot)
            page.fill("#opt_video_prompt", vp)
            for k in range(1, sheet["takes"] + 1):
                label = f"{shot['id']}_t{k}"
                ve.wait_for_slot()
                t0 = time.time()
                uuid = fr.create_video(vp, t0, {x["video_uuid"] for x in submitted})
                submitted.append({"label": label, "video_uuid": uuid, "duration": shot["dur"], "first": first,
                                  "last": prev_last, "submitted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))})
                (run_dir / "submitted.json").write_text(json.dumps(submitted, indent=1, ensure_ascii=False))
                ve.log(f"{label} submitted as {uuid} ({shot['dur']}s, first {first}, last {prev_last})")
        ve.log(f"all {len(submitted)} shot(s) submitted. Collect the clips with:\n"
               f"  python3 ve_collect.py --submitted {run_dir / 'submitted.json'} --out <dir>")
        ctx.close()


class Frames:
    """First Frame, Last Frame 對話框的操作（沿用 ve_runner.VE 的登入、片庫、關卡與名額控制）。"""

    def __init__(self, ve, R, aspect: str):
        self.ve, self.R, self.page = ve, R, ve.page
        self.ratio = 16 / 9 if aspect == "16:9" else 9 / 16

    def imgs(self) -> list[str]:
        """對話框裡已載好的生成圖。比例要和輸出比例相符：生成中的佔位圖是 3:2（2026-10-26 重做末格時被當成新圖）。"""
        return self.page.evaluate(f"""ar => {{ const r=({ROOT_JS})(); return [...r.querySelectorAll('img')]
            .filter(i=>i.naturalWidth>=500 && i.getBoundingClientRect().width>40 && !/\\.gif/i.test(i.src)
                       && Math.abs(i.naturalWidth/i.naturalHeight - ar) < 0.05*ar).map(i=>i.src); }}""", self.ratio)

    def js_click(self, js: str, what: str):
        if not self.page.evaluate(js):
            self.ve.shot_png(f"fail_{what.replace(' ', '_')}")
            raise RuntimeError(f"{what}: button not found")
        self.ve.log(what)

    def open_modal(self, aspect: str):
        self.js_click("""() => { const el=[...document.querySelectorAll('div')].filter(d=>d.children.length<8 &&
            /^First Frame, Last Frame/.test(d.textContent.trim())).map(d=>d.querySelector('button.btn-circle-big')).find(Boolean);
            if(!el) return false; el.click(); return true; }""", "open First Frame, Last Frame")
        self.page.wait_for_selector("#opt_video_prompt", state="visible", timeout=15_000)
        # 對話框自己的比例鈕（編輯器左側也有一組，不能點到那組）；真的滑鼠點，DOM click 只換 class
        self.page.evaluate(f"""a => {{ document.querySelectorAll('[data-fl-aspect]').forEach(x=>x.removeAttribute('data-fl-aspect'));
            const r=({ROOT_JS})(); r.querySelector(`button[data-value='${{a}}']`).setAttribute('data-fl-aspect','1'); }}""", aspect)
        self.page.locator("[data-fl-aspect='1']").click(force=True)
        self.page.wait_for_timeout(500)
        if not self.page.evaluate("() => document.querySelector(\"[data-fl-aspect='1']\").classList.contains('active')"):
            raise RuntimeError(f"aspect {aspect} did not become active")
        self.ve.log(f"dialog open, {aspect}")

    def set_first(self, lib_id: int):
        before = set(self.imgs())
        self.js_click("""() => { const b=document.querySelector('button.button-image-from-library[data-index="0"]');
            if(!b) return false; b.click(); return true; }""", "First Frame from Library")
        self.ve.open_folder("My AI Images")
        sel = f'.library-item[data-ident="{lib_id}"]'
        self.page.wait_for_selector(sel, state="attached", timeout=20_000)
        self.page.locator(sel).first.evaluate("el => el.click()")
        self.page.wait_for_timeout(500)
        self.js_click("""() => { const b=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Choose'
            && b.getBoundingClientRect().width>0).pop(); if(!b) return false; b.click(); return true; }""", f"first frame = {lib_id}")
        for _ in range(30):
            self.page.wait_for_timeout(500)
            if set(self.imgs()) - before:
                return
        raise RuntimeError(f"library image {lib_id} did not show up as the first frame")

    def make_last(self, label: str, prompt: str) -> str | None:
        """Smart Edit 從首格改出末格，關卡挑：回傳 src；r 重做；s 回 None。"""
        self.page.fill("#opt_image_prompt2", prompt)
        while True:
            before = set(self.imgs())
            self.js_click("""() => { const b=document.querySelector('button.button-frames-to-video-create[data-index="1"]');
                if(!b) return false; b.click(); return true; }""", "Create Last Image")
            new = []
            for _ in range(240):
                self.page.wait_for_timeout(1000)
                new = [s for s in self.imgs() if s not in before]
                if new:
                    break
            if not new:
                raise RuntimeError(f"last image never appeared (alerts: {self.ve.alerts()})")
            got = self.ve.qc_gate(f"{label}_last", new[:1])
            if got == self.R.SKIP:
                return None
            if got:
                return got

    def save_last(self, src: str) -> int:
        """末格存進 My AI Images，回傳 id（下一段 chain 用）：按這張圖旁的 Save Image，取存檔後最新的一張。"""
        t0 = time.time()
        self.ve.save_candidate(src)
        for _ in range(12):
            time.sleep(5)
            hits = [x for x in self.ve.library(self.R.IMG_CAT, "image") if self.R._utc(x["datetime"]) >= t0 - 5]
            if hits:
                item = max(hits, key=lambda x: (self.R._utc(x["datetime"]), x["id"]))
                self.ve.log(f"last frame saved as library image {item['id']}")
                return item["id"]
        raise RuntimeError(f"saved last frame never appeared in My AI Images (alerts: {self.ve.alerts()})")

    def set_duration(self, secs: int):
        self.page.evaluate("""v => { const r=document.querySelector('#opt_video_duration'); r.value=String(v);
            r.dispatchEvent(new Event('input',{bubbles:true})); r.dispatchEvent(new Event('change',{bubbles:true})); }""", secs)

    def create_video(self, vp: str, t0: float, known: set[str]) -> str:
        """送出後對話框不顯示 Video: uuid（2026-10-26 實測），改從片庫認：名稱是提示詞開頭、送出後建立、還沒記過的。"""
        self.js_click("""() => { const b=document.querySelector('button.button-frames-to-video'); if(!b) return false;
            b.click(); return true; }""", "Create Video")
        head = vp[:40]
        for _ in range(24):
            time.sleep(5)
            for x in self.ve.library(self.R.VID_CAT, "", 20):
                if (x.get("name") or "").startswith(head) and self.R._utc(x["datetime"]) >= t0 - 5 and x["uuid"] not in known:
                    return x["uuid"]
        self.ve.shot_png("submit_unconfirmed")
        raise RuntimeError(f"video never appeared in My AI Videos (alerts: {self.ve.alerts()})")


if __name__ == "__main__":
    main()
