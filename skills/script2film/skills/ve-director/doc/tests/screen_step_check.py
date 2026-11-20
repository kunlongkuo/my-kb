"""Does a rendered screen_step shot mark the right place at the right time (lecture-screen T2)?

  python3 screen_step_check.py <project> <beat id> [--theme lecture-light] [--box-only] [--shift-t S] [--shift-box PX]

Reads code_<theme>/<id>.marks.json (the boxes screen_step.js actually drew, and the screen's place in the frame, read
from the built page by doc_code.py), the beat's doc_screen log.json, and code_<theme>/<id>.mp4.
- box: each mark's centre, mapped back to 1920 x 1080 recording pixels, within BOX_PX of its logged element's centre.
  Prints `box ok N/N`.
- sync (webm beats; the selftest page's buttons turn from pure red to pure blue when clicked): in the rendered shot,
  every click shows red inside its mark at (t - clip[0]) - BEFORE and blue at + AFTER, same rule and numbers as
  screen_sync_check.py; and the first mark appears within FIRST_S of its click (the clip is cut so they meet).
  Prints `sync ok N/N`. --box-only skips it: a real site has no red / blue buttons.
--shift-t / --shift-box move the logged times / drawn boxes: the mutation self-test.
"""
import argparse, json, sys
from pathlib import Path

from screen_sync_check import AFTER, BEFORE, SHARE, frame, share

BOX_PX, FIRST_S = 8, 0.05


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project", type=Path)
    ap.add_argument("beat")
    ap.add_argument("--theme", default="lecture-light")
    ap.add_argument("--box-only", action="store_true", help="a real recording: check the boxes only")
    ap.add_argument("--shift-t", type=float, default=0.0)
    ap.add_argument("--shift-box", type=float, default=0.0)
    a = ap.parse_args()
    P, code = a.project, a.project / f"code_{a.theme}"
    spec = next(b for b in json.loads((P / "doc.json").read_text(encoding="utf-8"))["beats"] if b["id"] == a.beat)["params"]
    M = json.loads((code / f"{a.beat}.marks.json").read_text(encoding="utf-8"))
    log = {s["n"]: s for s in json.loads((P / spec["log"]).read_text(encoding="utf-8"))["steps"]} if spec.get("log") else {}
    sx, sy, sw, _ = M["screen"]
    k = 1920 / sw
    bad_box, bad_sync, n_sync = [], [], 0
    for s, m in zip(spec["steps"], M["marks"]):
        x, y, w, h = m["rect"]
        x, y = x + a.shift_box, y + a.shift_box
        got = ((x + w / 2 - sx) * k, (y + h / 2 - sy) * k)                 # mark centre in recording pixels
        bx, by, bw, bh = s["box"] if "box" in s else log[s["step"]]["box"]
        dist = ((got[0] - bx - bw / 2) ** 2 + (got[1] - by - bh / 2) ** 2) ** .5
        if dist > BOX_PX:
            bad_box.append(f"step {s['n']}: mark centre {dist:.1f} px from the element (need ≤ {BOX_PX})")
        if a.box_only or M["clip"] is None or "step" not in s or log[s["step"]]["do"] != "click":
            continue
        n_sync += 1
        tau = log[s["step"]]["t"] + a.shift_t - M["clip"][0]                # the click, in shot seconds
        pre = share(frame(code / f"{a.beat}.mp4", tau - BEFORE), [x, y, w, h], "red")
        post = share(frame(code / f"{a.beat}.mp4", tau + AFTER), [x, y, w, h], "blue")
        if pre < SHARE or post < SHARE:
            bad_sync.append(f"step {s['n']}: red {pre:.2f} at click-{BEFORE}, blue {post:.2f} at click+{AFTER} (need ≥ {SHARE})")
        if s is spec["steps"][0] and abs(tau - m["at"]) > FIRST_S:
            bad_sync.append(f"step {s['n']}: mark at {m['at']:.2f}s, click at {tau:.2f}s (need within {FIRST_S}s)")
    n = len(M["marks"])
    print("\n".join(bad_box + [f"box {'ok' if not bad_box else 'off'} {n - len(bad_box)}/{n}"]))
    if n_sync:
        print("\n".join(bad_sync + [f"sync {'ok' if not bad_sync else 'off'} {n_sync - len([b for b in bad_sync if 'red' in b])}/{n_sync}"]))
    sys.exit(1 if bad_box or bad_sync else 0)


if __name__ == "__main__":
    main()
