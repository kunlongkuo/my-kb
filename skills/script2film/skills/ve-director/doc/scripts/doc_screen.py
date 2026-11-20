"""Record a browser walkthrough headless: steps.json → screen.webm + a screenshot before every step + log.json.

  python3 doc_screen.py <steps.json> --out <folder> [--dry] [--profile <signed-in Chrome profile>]
steps.json: {"url": first page, "steps": [{"do": "goto", "url"} | {"do": "click", "sel"} | {"do": "type", "sel", "text"} |
{"do": "scroll", "y"} | {"do": "wait", "ms"}, ...]}; any step may carry "say" (the narration line it goes with).
A url with no scheme is a file next to steps.json; only http, https and file are accepted.
Output in <folder>: screen.webm (1920 x 1080), stepNN.png (the page just before step NN), log.json {"steps": [{"n", "do",
"t" (seconds from the recording's start, stamped right before the action), "box" (the element, 1920 x 1080 recording
pixels, for click / type), "url", "say"}]}. screen_step (scenes/screen_step.js) reads log.json to place its marks.
Login pages are never touched: an enabled, visible password field, or a url path containing login / signin / auth, after any step or
before typing stops the run with exit 3 ("login required: <url>") and keeps nothing; so does a step whose element never
shows (exit 1). --dry prints the pages it would open and
exits without starting a browser (show the list before recording).
"""
import argparse, json, shutil, sys, tempfile, time
from pathlib import Path
from urllib.parse import urlparse

from doc_common import read_json

W, H = 1920, 1080
ACTIONS = {"goto": ("url",), "click": ("sel",), "type": ("sel", "text"), "scroll": ("y",), "wait": ("ms",)}
SCHEMES = ("http", "https", "file")
LOGIN_WORDS = ("login", "signin", "auth")
SEL_WAIT_MS = 15000


def resolve(url, base):
    """A url with no scheme is a file path relative to the steps file's folder."""
    if urlparse(url).scheme:
        return url
    return (base / url).resolve().as_uri()


def load_steps(path):
    """steps.json → (first url, steps) with urls resolved; stops on an unknown action, a missing field or a scheme
    outside SCHEMES."""
    path = Path(path)
    spec = read_json(path)
    steps = [dict(s) for s in spec.get("steps", [])]
    for n, s in enumerate(steps, 1):
        need = ACTIONS.get(s.get("do"))
        if need is None:
            sys.exit(f"✗ step {n}: do must be one of {', '.join(ACTIONS)}: {s.get('do')!r}")
        miss = [k for k in need if k not in s]
        if miss:
            sys.exit(f"✗ step {n} ({s['do']}): missing {', '.join(miss)}")
        if s["do"] == "goto":
            s["url"] = resolve(s["url"], path.parent)
    first = resolve(spec["url"], path.parent)
    for u in [first] + [s["url"] for s in steps if s["do"] == "goto"]:
        if urlparse(u).scheme not in SCHEMES:
            sys.exit(f"✗ only {', '.join(SCHEMES)} urls: {u}")
    return first, steps


def pages(first, steps):
    """The pages the run opens, in order (what --dry prints)."""
    return [first] + [s["url"] for s in steps if s["do"] == "goto"]


def is_login_url(url):
    path = urlparse(url).path.lower()
    return any(w in path for w in LOGIN_WORDS)


def login_page(page):
    """The url when the page is a login page, else None. Only a password field that can be typed into counts: a
    settings dialog keeps disabled ones (VideoExpress Profile, "Change password" unticked, 2026-10-28)."""
    if is_login_url(page.url) or page.locator("input[type=password]:not([disabled])").filter(visible=True).count():
        return page.url
    return None


REC = dict(viewport={"width": W, "height": H}, device_scale_factor=1, record_video_size={"width": W, "height": H})


def open_context(pw, video_dir, profile=None):
    """A recording context at 1920 x 1080 and scale 1, so element boxes are already in recording pixels. (context,
    browser to close or None). With profile (a Chrome user-data folder that is already signed in, e.g. ve-runner's
    .profile; lecture-screen T5, chosen over typing passwords): a throwaway copy of it, so the original is
    never locked or changed (a nightly run may be using it) and its page zoom goes back to 100 %."""
    if profile is None:
        browser = pw.chromium.launch(headless=True)
        return browser.new_context(record_video_dir=str(video_dir), **REC), browser
    copy = Path(tempfile.mkdtemp(prefix="doc_screen_profile_"))
    shutil.copytree(profile, copy, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("Singleton*", "RunningChromeVersion", "*Cache*", "Service Worker", "*.log"))
    prefs = copy / "Default" / "Preferences"
    if prefs.exists():
        data = json.loads(prefs.read_text(encoding="utf-8"))
        data.get("partition", {}).get("default_zoom_level", {}).pop("x", None)
        prefs.write_text(json.dumps(data), encoding="utf-8")
    ctx = pw.chromium.launch_persistent_context(str(copy), channel="chrome", headless=True,
                                                record_video_dir=str(video_dir), **REC)
    ctx._doc_screen_copy = copy
    return ctx, None


def run(first, steps, out, profile=None):
    from playwright.sync_api import TimeoutError as Timeout, sync_playwright
    made = not out.exists()
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / ".video"
    log, stop, shots, fail = [], None, [], None
    with sync_playwright() as pw:
        ctx, browser = open_context(pw, tmp, profile)
        page = ctx.new_page()
        t0 = time.monotonic()                      # the video starts with the page, not the context (T1 measured)
        page.goto(first, wait_until="load")
        stop = login_page(page)
        for n, s in enumerate(steps, 1):
            if stop:
                break
            # the first visible match: sites keep hidden copies of links (GitHub's file list, 2026-10-28)
            loc = page.locator(s["sel"]).filter(visible=True).first if "sel" in s else None
            box = None
            if loc is not None:
                try:
                    loc.wait_for(state="visible", timeout=SEL_WAIT_MS)
                except Timeout:
                    fail = f"✗ step {n} ({s['do']}): no visible element for {s['sel']!r} on {page.url}"
                    break
                b = loc.bounding_box()
                box = [round(b["x"], 1), round(b["y"], 1), round(b["width"], 1), round(b["height"], 1)]
            shots.append(out / f"step{n:02d}.png")
            page.screenshot(path=str(shots[-1]))
            if s["do"] == "type" and login_page(page):
                stop = page.url
                break
            t = round(time.monotonic() - t0, 3)    # stamped after the screenshot, right before the action
            if s["do"] == "goto":
                page.goto(s["url"], wait_until="load")
            elif s["do"] == "click":
                loc.click()
            elif s["do"] == "type":
                loc.fill(s["text"])
            elif s["do"] == "scroll":
                page.mouse.wheel(0, s["y"])
            else:
                page.wait_for_timeout(s["ms"])
            log.append({"n": n, "do": s["do"], "t": t, "box": box, "url": page.url, "say": s.get("say")})
            stop = login_page(page)
        video = page.video.path()
        ctx.close()
        if browser:
            browser.close()
        shutil.rmtree(getattr(ctx, "_doc_screen_copy", tmp / "-"), ignore_errors=True)
    if stop or fail:                               # keep nothing: only what this run wrote is removed
        for f in shots:
            f.unlink(missing_ok=True)
        shutil.rmtree(tmp, ignore_errors=True)
        if made:
            out.rmdir()
        if fail:
            sys.exit(fail)
        print(f"login required: {stop}")
        sys.exit(3)
    Path(video).rename(out / "screen.webm")
    shutil.rmtree(tmp)
    (out / "log.json").write_text(json.dumps({"size": [W, H], "steps": log}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out}: screen.webm, {len(log)} steps")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("steps")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--dry", action="store_true", help="print the pages it would open, start no browser")
    ap.add_argument("--profile", type=Path, help="a signed-in Chrome user-data folder to copy (never changed)")
    a = ap.parse_args()
    first, steps = load_steps(a.steps)
    if a.dry:
        print("\n".join(pages(first, steps)))
        return
    run(first, steps, a.out, a.profile)


if __name__ == "__main__":
    main()
