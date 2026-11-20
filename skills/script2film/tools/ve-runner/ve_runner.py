#!/usr/bin/env python3
"""VideoExpress run-sheet executor (no LLM in the loop).

Reads a PromptStudio storyboard / run sheet (markdown) and drives
app.videoexpress.ai with Playwright: one master image per cast actor (saved in
My AI Images), then per shot: Reference Photo 1/2 = that shot's cast masters ->
Create Image -> HUMAN QC (pick candidate / re-roll) -> set duration ->
Create Video (a shot with a spoken line uses Lipsync HD; --speech-in-prompt keeps the normal path with sound) -> record the job uuid
in runs/<ts>/submitted.json for ve_collect.py. The generation dialog stays open
for the whole run (reopening it resets every option and both reference slots).

Run sheet per shot: optional "- **Cast:** Actor 2, Actor 1" (slot order; default =
actors named in the image prompt) and "- **Start:** master | chain | same | image <file>" (image: animate that file, uploaded to Media Library > Images; chain: start from the previous shot's last frame;
same: animate the previous shot's first frame again with this shot's video prompt, for A/B prompt tests).
"- **Save:** master" saves the picked first frame in My AI Images (runs/<ts>/saved.json) and submits no video:
a reference-locked image, e.g. a turnaround sheet drawn from an existing master, becomes a new master.
"- **Narration:** b3.wav" renders the clip against that audio (≤ 10 s) through VE's Narration Video path.

Usage:
  python3 ve_runner.py samples/indigo-dancer.md            # full run
  python3 ve_runner.py samples/indigo-dancer.md --shots 1   # only shot 1
  python3 ve_runner.py x.md --masters runs/<ts>/masters.json # reuse masters from an earlier run
  python3 ve_runner.py x.md --run-dir ../film/ve-runs       # put runs/<ts>/ in the film's folder instead
  python3 ve_runner.py --inspect                            # dump modal DOM, no generation
  python3 ve_runner.py x.md --step                          # pause before every click

First run: the script opens Chrome (persistent profile in ./.profile) and
waits for you to log in. Log in yourself; the script never touches credentials.
"""
from __future__ import annotations
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()

import argparse
import calendar
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

HERE = Path(__file__).resolve().parent
APP_URL = "https://app.videoexpress.ai/"
PAGE_ZOOM = 0.9  # Chrome page zoom; keeps Retina sharpness, unlike --force-device-scale-factor
# Headless by default (2026-11-12, user's choice: no window to click by accident; memory is about the same, see
# NOTES.md). It has no real window, so it needs a fixed viewport. S2F_VE_HEADED=1 opens a window instead: needed to log
# in by hand when the session has expired. Headed, the page follows the real window (a fixed viewport larger than
# the screen clips the bottom/right), and there are no automation / --no-sandbox warning bars.


def headed(environ) -> bool:
    """Open a window? When S2F_VE_HEADED is set (non-empty) only it counts ("1" opens one); otherwise the old name
    VE_HEADED == "1"."""
    if environ.get("S2F_VE_HEADED"):
        return environ["S2F_VE_HEADED"] == "1"
    return environ.get("VE_HEADED") == "1"


HEADED = headed(os.environ)


def never_logged_in(profile: Path) -> bool:
    """No cookie file in the profile: Chrome has never been run on it, so there is no VideoExpress login to use."""
    return not (profile / "Default" / "Cookies").exists()


LOGIN_HINT = ("no VideoExpress login on this machine yet ({profile} has no cookies). Open a window once and let the user "
              "log in there: S2F_VE_HEADED=1 python3 tools/ve-runner/ve_runner.py --login (it waits up to 10 minutes "
              "for the login, then closes). After that the default, without a window, works.")


def wait_for_enter(is_headed, isatty):
    """Hold the browser open at the end for a look? Only with a window and a terminal: headless there is nothing to look
    at, and an agent's pseudo-terminal would wait for an Enter that never comes (s2f-3d-host-late-reveal D3)."""
    return bool(is_headed and isatty)
BROWSER_OPTS = dict(
    channel="chrome", headless=False, no_viewport=True, chromium_sandbox=True,
    args=["--window-size=1600,1100"],
    ignore_default_args=["--enable-automation"],
)
if not HEADED:
    BROWSER_OPTS.update(headless=True, no_viewport=False, viewport={"width": 1600, "height": 1100})


def launch_browser(pw, profile: Path):
    """Chrome on the persistent profile (headless unless S2F_VE_HEADED=1), with PAGE_ZOOM as the default zoom."""
    prefs = profile / "Default" / "Preferences"
    prefs.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(prefs.read_text()) if prefs.exists() else {}
    data.setdefault("partition", {}).setdefault("default_zoom_level", {})["x"] = math.log(PAGE_ZOOM, 1.2)
    prefs.write_text(json.dumps(data))
    return pw.chromium.launch_persistent_context(str(profile), **BROWSER_OPTS)


IMG_CAT, VID_CAT = "557394", "557393"  # Media Library folders "My AI Images" / "My AI Videos"
LIST_URL = APP_URL + ("api/library/get_media/4?categoryId={cat}&page=1&start=0&limit={n}"
                      "&query=&orderBy=id&orderDir=desc&filter={f}")
MAX_IN_FLIGHT = 5  # per account; VE drops over-cap video jobs silently, with no library record


class Dropped(RuntimeError):
    """a submitted video job never reached the library (over the concurrency cap)."""
    def __init__(self, msg: str, uuid: str = ""):
        super().__init__(msg)
        self.uuid = uuid


NARRATION_MAX = 10.0  # seconds: the Import Audio tab says "The maximum audio duration 0.1 minutes (10 seconds)"


def audio_seconds(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def _utc(stamp: str) -> float:
    """library 'datetime' (UTC, '+00:00') -> epoch seconds."""
    return calendar.timegm(time.strptime(stamp[:19], "%Y-%m-%dT%H:%M:%S"))


# ---------------------------------------------------------------- run sheet


@dataclass
class Shot:
    n: int
    duration: int
    t2i: str
    i2v: str
    speech: list[tuple[int, str]] = field(default_factory=list)  # (actor number, spoken line), in prompt order
    cast: list[str] = field(default_factory=list)  # ["Actor 1", "Actor 2"] -> Reference Photo 1, 2
    start: str = "master"                          # master | chain | same | image
    start_image: str = ""                          # Start: image <file>: absolute path of the frame to animate
    save: str = ""                                 # "" | master (save the picked frame, no video)
    narration: str = ""                            # absolute path of this shot's narration audio (≤ 10 s), or ""

    @property
    def dialogue(self) -> str | None:
        return self.speech[0][1] if self.speech else None


@dataclass
class RunSheet:
    actors: list[str] = field(default_factory=list)
    shots: list[Shot] = field(default_factory=list)


SKIP = "skip"  # qc_gate's answer for "no video for this shot"


class NoCandidates(RuntimeError):
    """Create Image produced nothing within its wait (seen when the account cap was full)."""


DIALOGUE_RE = re.compile(r'says in [^:"]*:\s*"([^"]+)"')
BULLET_RE = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.*)$")


def parse_runsheet(path: Path) -> RunSheet:
    rs = RunSheet()
    cur: dict | None = None
    section = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            section = line[2:].strip().lower()
            continue
        if line.startswith("## Shot"):
            if cur:
                rs.shots.append(_shot(cur, path.parent))
            cur = {"n": int(re.search(r"\d+", line).group())}
            continue
        if "actor portrait" in section and re.match(r"^Actor \d+:", line):
            rs.actors.append(line.split(":", 1)[1].strip())
            continue
        m = BULLET_RE.match(line)
        if m and cur is not None:
            cur[m.group(1).strip().lower()] = m.group(2).strip()
    if cur:
        rs.shots.append(_shot(cur, path.parent))
    if not rs.actors and any(s.cast for s in rs.shots):
        sys.exit("run sheet casts actors but has no 'Actor N:' portrait line")
    if not rs.shots:
        sys.exit("run sheet has no '## Shot N' blocks")
    return rs


def _speech(n: int, i2v: str) -> list[tuple[int, str]]:
    """spoken lines in the video prompt, each with its speaker: the last "Actor N" named before the line.
    Lipsync HD takes one line per actor (Actor 1 Script, Actor 2 Script), so a shot has at most two lines, by two actors."""
    out = []
    for m in DIALOGUE_RE.finditer(i2v):
        who = re.findall(r"Actor\s*(\d+)", i2v[:m.start()])
        out.append((int(who[-1]) if who else 1, m.group(1)))
    return out


def _check_lipsync(n: int, speech: list[tuple[int, str]]) -> None:
    """Lipsync HD limits, checked only on the Lipsync path: with --speech-in-prompt the lines stay in the video
    prompt, so one actor may speak in several timed beats ([ACTION 0-2s] ... says: "...", [ACTION 2-4s] ... says:
    "..."; user-tested 2026-11-08 to split a long line cleanly)."""
    if len(speech) > 2:
        sys.exit(f"shot {n}: {len(speech)} spoken lines; Lipsync HD takes one line per actor, two actors at most "
                 "(use --speech-in-prompt for timed multi-beat lines)")
    if len(speech) == 2 and sorted(a for a, _ in speech) != [1, 2]:
        sys.exit(f"shot {n}: two spoken lines must be one by Actor 1 and one by Actor 2, got speakers "
                 f"{[a for a, _ in speech]} (use --speech-in-prompt for timed multi-beat lines)")


def _shot(d: dict, base: Path) -> Shot:
    dur = int(re.search(r"\d+", d.get("duration", "5")).group())
    i2v = d.get("image-to-video prompt", "")
    t2i = d.get("text-to-image prompt", "")
    speech = _speech(d["n"], i2v)
    # Cast: explicit "- **Cast:** Actor 2, Actor 1" / "none"; otherwise the actors named in the
    # image prompt, in order of first mention (max 2: VE has two reference slots)
    if "cast" in d:
        cast = [] if d["cast"].strip().lower() in ("", "none", "無") else \
            [f"Actor {n}" for n in re.findall(r"Actor\s*(\d+)", d["cast"])]
    else:
        seen = sorted(set(re.findall(r"Actor\s*(\d+)", t2i)), key=lambda n: t2i.find(f"Actor {n}"))
        cast = [f"Actor {n}" for n in seen]
    if len(cast) > 2:
        sys.exit(f"shot {d['n']}: cast {cast} has more than 2 reference-bound actors")
    start, start_image = d.get("start", "master").strip(), ""
    if start.lower().startswith("image "):
        # Start: image <file>: a frame made outside VE (a candidate retouched by hand, 2026-10-22) is uploaded to
        # Media Library > Images and animated via Use from Library; no image is generated, so no Cast
        f = Path(start[6:].strip()).expanduser()
        f = f if f.is_absolute() else base / f
        if not f.is_file():
            sys.exit(f"shot {d['n']}: start image not found: {f}")
        # VE refuses any other shape ("Aspect ratio needs to be 16:9 or 9:16") after the upload, deep in the run
        # (2026-11-05: a portrait Tissot painting for 044 Absalom); stop here instead
        try:
            from PIL import Image
            w, h = Image.open(f).size
            if not any(abs(w / h - r) < .01 for r in (16 / 9, 9 / 16)):
                sys.exit(f"shot {d['n']}: start image must be 16:9 or 9:16 (VE refuses others), got {w}x{h}: {f}"
                         " (pad it: picture centred, blurred copy filling the sides)")
        except ImportError:
            pass
        start, start_image = "image", str(f.resolve())
    start = start.lower()
    if start not in ("master", "chain", "same", "image"):
        sys.exit(f"shot {d['n']}: Start must be 'master', 'chain', 'same' or 'image <file>', got {start!r}")
    save = d.get("save", "").strip().lower()
    if save not in ("", "master"):
        sys.exit(f"shot {d['n']}: Save must be 'master', got {save!r}")
    if save and start != "master":
        sys.exit(f"shot {d['n']}: Save: master needs a generated image (Start: master), got Start {start!r}")
    # Narration: an audio file (relative to the sheet) that VE's Narration Video path renders the clip against
    narration = ""
    if d.get("narration", "").strip():
        f = Path(d["narration"].strip()).expanduser()
        f = f if f.is_absolute() else base / f
        if not f.is_file():
            sys.exit(f"shot {d['n']}: narration audio not found: {f}")
        if speech:
            sys.exit(f"shot {d['n']}: a narrated shot cannot also have a spoken line (both use VE's talking-video button)")
        if save:
            sys.exit(f"shot {d['n']}: Save: master submits no video, so it cannot carry a narration")
        narration = str(f.resolve())
    return Shot(
        n=d["n"],
        duration=max(3, min(10, dur)),
        t2i=t2i,
        i2v=i2v,
        speech=speech,
        cast=cast,
        start=start,
        start_image=start_image,
        save=save,
        narration=narration,
    )


# ---------------------------------------------------------------- browser helpers


class VE:
    def __init__(self, page: Page, run_dir: Path, step: bool, auto_pick: bool = False, aspect: str = "16:9"):
        self.page = page
        self.ref_folder = "My AI Images"   # where reference-slot ids live (see --ref-folder)
        self.aspect = aspect  # "16:9" | "9:16", the dialog's own Landscape / Vertical toggle
        self.auto_pick = auto_pick  # accept candidate 1 at every QC gate (official VOX workflow: first take ships)
        self.run_dir = run_dir
        self.step = step
        self._gif: dict[str, bool] = {}
        # Every candidate returned so far, by src and by content: the candidate carousel hides older
        # sets and shows them again later, so "not on screen before the click" is not "new".
        self._seen_srcs: set[str] = set()
        self._before_image: set[str] = set()  # srcs in the dialog before the latest Create Image
        self._last_cands: list[str] = []  # candidates the latest Create Image returned
        self._seen_hashes: set[str] = set()
        self.slot_ids: list[int | None] = [None, None]   # library id held by Reference Photo 1 / 2
        self.slot_srcs: list[str | None] = [None, None]  # slot thumbnail src right after picking

    # -- logging / pausing
    def log(self, msg: str):
        stamp = time.strftime("%H:%M:%S")
        print(f"[{stamp}] {msg}", flush=True)
        with (self.run_dir / "run.log").open("a") as f:
            f.write(f"{stamp} {msg}\n")

    def shot_png(self, name: str):
        p = self.run_dir / f"{name}.png"
        self.page.screenshot(path=str(p))
        return p

    def pause(self, what: str):
        if self.step and sys.stdin.isatty():
            input(f"  [step] about to: {what}  (Enter to continue) ")

    def ask(self, prompt: str, allowed: str) -> str:
        """Interactive answer; without a TTY, wait for runs/<ts>/decision.txt."""
        if sys.stdin.isatty():
            while True:
                a = input(prompt).strip().lower()
                if a and a[0] in allowed:
                    return a[0]
        dfile = self.run_dir / "decision.txt"
        dfile.unlink(missing_ok=True)
        self.log(f"QC WAITING: write one of [{allowed}] to {dfile}")
        while True:
            time.sleep(2)
            if dfile.exists():
                a = dfile.read_text().strip().lower()
                dfile.unlink(missing_ok=True)
                if a and a[0] in allowed:
                    self.log(f"decision: {a[0]}")
                    return a[0]
                self.log(f"ignored decision {a!r}")

    # -- DOM primitives (DOM click is what the modal buttons reliably accept)
    def dom_click(self, selector: str):
        self.pause(f"click {selector}")
        self.page.locator(selector).first.evaluate("el => el.click()")

    def set_checkbox(self, name: str, on: bool):
        loc = self.page.locator(f"input[name={name}]").first
        if loc.is_checked() != on:
            self.pause(f"toggle {name} -> {on}")
            loc.evaluate("el => el.click()")
        if loc.is_checked() != on:
            raise RuntimeError(f"checkbox {name} refused state {on}")

    def fill(self, selector: str, text: str):
        self.pause(f"fill {selector} ({len(text)} chars)")
        self.page.fill(selector, text)
        got = self.page.input_value(selector)
        if got != text:
            raise RuntimeError(f"{selector} did not accept the text")

    # -- app-level steps
    def open_app(self):
        self.page.goto(APP_URL)
        if HEADED:
            self.log("waiting for editor (log in manually if prompted; 10 min max)")
            self.page.wait_for_selector("text=Create Video From Prompt", timeout=600_000)
        else:
            self.log("waiting for editor (headless; 90 s max)")
            try:
                self.page.wait_for_selector("text=Create Video From Prompt", timeout=90_000)
            except Exception:
                raise RuntimeError("editor did not open without a window: the login has probably expired. "
                                   "Run once with S2F_VE_HEADED=1, log in by hand, then run again.") from None
        close = self.page.locator("button:text-is('Close')")
        if close.count() and close.first.is_visible():
            close.first.evaluate("el => el.click()")
        self.log("editor ready")

    def dismiss_news(self):
        # the "Latest News and Updates" side panel can pop up at any time and sits over the modal
        # scope to that panel: the generator modal has its own "Close" button
        hit = self.page.evaluate(
            """() => {
              const b=[...document.querySelectorAll('button')].find(b=>{
                if(b.textContent.trim()!=='Close'||!b.offsetParent) return false;
                for(let e=b.parentElement;e;e=e.parentElement){
                  if(e.querySelector('#opt_prompt')) return false;
                  if(/Latest News and Updates/.test(e.textContent)) return true;
                }
                return false;});
              if(b){b.click();return true;} return false;
            }"""
        )
        if hit:
            self.log("news panel dismissed")
            self.page.wait_for_timeout(500)

    def open_modal(self):
        self.dismiss_news()
        if self.page.locator("#opt_prompt").is_visible():
            self.set_checkbox("shared", False)
            self.set_aspect()
            return
        # the card's round arrow button sits next to the card title
        self.page.evaluate(
            """() => {
              const el=[...document.querySelectorAll('div')]
                .filter(d=>d.children.length<8 && /Create Video From Prompt/.test(d.textContent))
                .map(d=>d.querySelector('button.btn-circle-big')).find(Boolean);
              if(!el) throw new Error('generator card button not found');
              el.click();
            }"""
        )
        self.page.wait_for_selector("#opt_prompt", state="visible", timeout=15_000)
        # gallery share must be OFF (re-verify on every modal open)
        self.set_checkbox("shared", False)
        self.set_aspect()  # reopening resets it like every other option
        self.log(f"modal open, gallery share OFF, {self.aspect}")

    def set_aspect(self):
        """Click the dialog's Landscape 16:9 / Vertical 9:16 button and verify that same button became active. The editor
        has its own canvas pair (left panel); the dialog's pair is the one nearest #opt_prompt (2026-10-11: a
        12-levels-up search hit the editor's pair and turned the project canvas vertical)."""
        want = {"16:9": "Landscape16:9", "9:16": "Vertical9:16"}[self.aspect]
        ok = self.page.evaluate(
            """want => {
              const ta=document.querySelector('#opt_prompt'); if(!ta) return 'no dialog';
              // nearest match to the prompt box: the editor's own canvas toggle sits further out and must not be hit
              let b=null;
              for(let root=ta.parentElement; root && !b; root=root.parentElement)
                b=[...root.querySelectorAll('button')].find(x=>x.textContent.replace(/\\s+/g,'')===want
                        && x.getBoundingClientRect().width>0);
              if(!b) return 'no button';
              document.querySelectorAll('[data-ve-aspect]').forEach(x=>x.removeAttribute('data-ve-aspect'));
              b.setAttribute('data-ve-aspect','1');
              window.__veAspectBtn=b;
              return 'ok';
            }""",
            want,
        )
        if ok != "ok":
            raise RuntimeError(f"aspect {self.aspect}: {ok}")
        # a real mouse click, as a person would: a DOM .click() can flip the class without VE taking the setting
        self.pause(f"aspect -> {self.aspect}")
        self.page.locator("[data-ve-aspect='1']").click()
        self.page.wait_for_timeout(500)
        active = self.page.evaluate("() => !!(window.__veAspectBtn && window.__veAspectBtn.classList.contains('active'))")
        if not active:
            raise RuntimeError(f"aspect {self.aspect}: button did not become active")

    def modal_images(self) -> list[str]:
        """srcs of generated-image candidates currently shown in the modal."""
        return self.page.evaluate(
            """() => {
              const ta=document.querySelector('#opt_prompt'); if(!ta) return [];
              let root=ta; for(let i=0;i<8&&root.parentElement;i++) root=root.parentElement;
              return [...root.querySelectorAll('img')]
                .filter(i=>i.naturalWidth>=800 && i.getBoundingClientRect().width>60
                        && !/\\.gif(\\?|$)/i.test(i.src))
                .map(i=>i.src);
            }"""
        )

    def all_modal_srcs(self) -> list[str]:
        """every img src in the dialog, hidden carousel pages included (for the before-click snapshot)."""
        return self.page.evaluate(
            """() => {
              const ta=document.querySelector('#opt_prompt'); if(!ta) return [];
              let root=ta; for(let i=0;i<8&&root.parentElement;i++) root=root.parentElement;
              return [...root.querySelectorAll('img')].map(i=>i.src).filter(Boolean);
            }"""
        )

    def _fresh(self, srcs: list[str]) -> dict[str, str]:
        """{src: sha1} of the candidates whose bytes match none already returned (same image, new src)."""
        out = {}
        for s in srcs:
            try:
                h = hashlib.sha1(self.page.request.get(s).body()).hexdigest()
            except Exception:  # noqa: BLE001  not fetchable yet: judge it on the next poll
                continue
            if h not in self._seen_hashes:
                out[s] = h
        return out

    def alerts(self) -> list[str]:
        """visible toast / alert texts (VE reports refusals this way, e.g. a missing reference photo)."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll('.toast,.alert,.swal2-popup,.noty_body,.notification,[role=alert]')]
                 .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0})
                 .map(e=>e.textContent.trim().replace(/^×/,'').replace(/\\s+/g,' ').slice(0,200)).filter(Boolean)"""
        )

    def create_image(self, prompt: str, image_type: str, enhance: bool, creative: bool = False) -> list[str]:
        self.dismiss_news()
        self.fill("#opt_prompt", prompt)
        # Creative mode disables the Image Type select: unlock it, pick the type, then set Creative
        self.set_checkbox("image_creative_mode", False)
        self.page.select_option("select.select-type", image_type)
        self.set_checkbox("auto_enhance_prompt", enhance)
        self.set_checkbox("image_creative_mode", creative)
        before = set(self.all_modal_srcs()) | self._seen_srcs
        self._before_image = before  # select_candidate: a frame from here is not this shot's
        seen_alerts = set(self.alerts())
        self.dom_click("button:has-text('Create Image')")
        self.log("Create Image sent; waiting for candidates (up to 4 min)")
        deadline = time.time() + 240
        last, stable_since = [], None
        while time.time() < deadline:
            time.sleep(3)
            new_alerts = [a for a in self.alerts() if a not in seen_alerts]
            if any(re.search(r"please|error|fail", a, re.I) for a in new_alerts):
                self.shot_png("create_image_refused")
                raise RuntimeError(f"Create Image refused: {new_alerts}")
            imgs = self.modal_images()
            now = [s for s in imgs if s not in before and not self._is_gif(s)]
            # 2026-11-09 (one shot of a short film): one candidate looked stable while the second was still the
            # generating GIF; it landed after the pick, moved the carousel and select_candidate stopped the run.
            # Wait until no generating placeholder is left in the dialog.
            if any(self._is_gif(s) for s in imgs):
                last, stable_since = now, time.time()
                continue
            if now != last:
                last, stable_since = now, time.time()
                continue
            # the generating placeholder is a 400x225 GIF; accept only real images
            # whose set has not changed for 6 s (later candidates may still land)
            if now and time.time() - stable_since >= 6:
                fresh = self._fresh(now)
                if len(fresh) < len(now):
                    self.log(f"ignored {len(now) - len(fresh)} candidate(s) identical to earlier ones")
                    before |= set(now) - set(fresh)
                    last = list(fresh)
                    if not fresh:
                        continue
                self._seen_srcs.update(fresh)
                self._seen_hashes.update(fresh.values())
                self.log(f"{len(fresh)} candidate(s)")
                self._last_cands = list(fresh)
                return list(fresh)
        raise NoCandidates("no image candidates appeared within 4 min")

    def _is_gif(self, src: str) -> bool:
        if src not in self._gif:
            try:
                self._gif[src] = self.page.request.get(src).body()[:4] == b"GIF8"
            except Exception:  # noqa: BLE001
                return False  # not cached: retried on the next poll
        return self._gif[src]

    # -- media library (same logged-in context, so page.request carries the session)
    def library(self, cat: str, f: str = "", n: int = 40) -> list[dict]:
        for attempt in range(4):
            try:
                return self.page.request.get(LIST_URL.format(cat=cat, n=n, f=f), timeout=60_000).json()["results"]
            except Exception as e:  # noqa: BLE001  transient "socket hang up"
                self.log(f"library list failed ({str(e).splitlines()[0][:80]}), retry {attempt + 1}")
                time.sleep(10)
        raise RuntimeError("media library API unreachable")

    def save_candidate(self, src: str):
        """click the Save Image button that belongs to this candidate (nearest ancestor holding one)."""
        self.page.evaluate(
            """src => { const img=[...document.querySelectorAll('img')].find(i=>i.src===src);
                       if(!img) throw new Error('candidate img vanished');
                       for(let e=img.parentElement;e;e=e.parentElement){
                         const b=e.querySelector('.button-save-image'); if(b){b.click();return;} }
                       throw new Error('no Save Image button near candidate'); }""",
            src,
        )

    def save_to_library(self, src: str, prompt: str) -> dict:
        """Save Image on this candidate and return its My AI Images item.
        Candidates are NOT auto-saved, the library re-encodes them (byte size differs) and images
        carry no uuid; an item is named after the first ~60 characters of its prompt. So: the item
        whose name is a prefix of our prompt, created at or after our Save click."""
        t0 = time.time()
        seen = set(self.alerts())
        self.save_candidate(src)
        already = False
        for _ in range(10):
            self.page.wait_for_timeout(1000)
            new = [a for a in self.alerts() if a not in seen]
            if any("already been saved" in a for a in new):
                already = True
                break
            if any("saved" in a for a in new):
                break

        if already:  # an earlier save of a same-named image would be indistinguishable: do not guess
            raise RuntimeError("VE says this image was already saved; pass its library id with --masters")
        for _ in range(8):
            hits = [x for x in self.library(IMG_CAT, "image")
                    if x.get("name") and prompt.startswith(x["name"]) and _utc(x["datetime"]) >= t0 - 5]
            if hits:
                item = max(hits, key=lambda x: _utc(x["datetime"]))
                self.log(f"saved as library image {item['id']} ({item['fileName']})")
                return item
            time.sleep(5)
        raise RuntimeError("saved candidate never appeared in My AI Images")

    # -- Consistent Character reference slots
    def slots(self) -> list[dict]:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('.consistent-character-image-container .select-image-container')]
                 .map(c=>{const w=c.querySelector('.overflow-hidden'); const i=w&&w.querySelector('img');
                          return {filled: !!w && !w.classList.contains('hidden'), src: i? i.src : null};})"""
        )

    def clear_slot(self, k: int):
        self.page.locator(".consistent-character-image-container .button-select-image-clear").nth(k) \
            .evaluate("el => el.click()")
        self.page.wait_for_timeout(800)
        if self.slots()[k]["filled"]:
            raise RuntimeError(f"Reference Photo {k + 1} did not clear")
        self.slot_ids[k] = self.slot_srcs[k] = None

    def pick_reference(self, k: int, lib_id: int):
        """Reference Photo k+1 -> Select Image -> self.ref_folder (My AI Images, or Images for an uploaded photo,
        --ref-folder) -> item lib_id -> Choose; verify the thumbnail."""
        self.pause(f"pick library image {lib_id} into Reference Photo {k + 1}")
        self.page.locator("button.button-reference-photo2").nth(k).evaluate("el => el.click()")
        self.page.wait_for_function(  # folders are listed a few seconds after the dialog opens
            "n => [...document.querySelectorAll('.library-folder-title')].some(e=>e.textContent.trim()===n)",
            arg=self.ref_folder, timeout=20_000)
        self.page.evaluate("""n => [...document.querySelectorAll('.library-folder-title')]
                                .find(e=>e.textContent.trim()===n).click()""", self.ref_folder)
        sel = f'.library-item[data-ident="{lib_id}"]'
        for _ in range(6):  # older items sit behind "More"
            try:
                self.page.wait_for_selector(sel, state="attached", timeout=6_000)
                break
            except PWTimeout:
                more = self.page.locator("button:has-text('More'):visible")
                if not more.count():
                    break
                more.first.evaluate("el => el.click()")
        if not self.page.locator(sel).count():
            self.shot_png(f"ref{k + 1}_not_found")
            raise RuntimeError(f"library image {lib_id} not found in {self.ref_folder}")
        self.page.locator(sel).first.evaluate("el => el.click()")
        self.page.wait_for_timeout(500)
        self.page.evaluate("""() => { const b=[...document.querySelectorAll('button')]
                                .filter(b=>b.textContent.trim()==='Choose'&&b.getBoundingClientRect().width>0).pop();
                              if(!b) throw new Error('Choose button not found'); b.click(); }""")
        for _ in range(20):
            self.page.wait_for_timeout(500)
            s = self.slots()[k]
            if s["filled"] and s["src"] and "icon-image" not in s["src"]:
                self.slot_ids[k], self.slot_srcs[k] = lib_id, s["src"]
                self.log(f"Reference Photo {k + 1} = library image {lib_id}")
                return
        self.shot_png(f"ref{k + 1}_empty")
        raise RuntimeError(f"Reference Photo {k + 1} stayed empty after choosing {lib_id}")

    def ensure_cast(self, ids: list[int]):
        """make the reference slots hold exactly these library images (in slot order) — or CC off when empty.
        The dialog keeps slots while it stays open; re-pick only an empty or mismatched slot."""
        if not ids:
            self.set_checkbox("use_consistent_character", False)
            return
        self.set_checkbox("use_consistent_character", True)
        self.page.wait_for_timeout(500)
        for k in (0, 1):
            want = ids[k] if k < len(ids) else None
            cur = self.slots()[k]
            ok = (not cur["filled"]) if want is None else \
                (cur["filled"] and self.slot_ids[k] == want and cur["src"] == self.slot_srcs[k])
            if ok:
                continue
            if cur["filled"]:
                self.clear_slot(k)
            if want is not None:
                self.pick_reference(k, want)

    def active_frame(self) -> str | None:
        """src of the image on the dialog's active carousel slide: the frame Create Video animates."""
        return self.page.evaluate(
            """() => { const ta=document.querySelector('#opt_prompt'); if(!ta) return null;
                       let root=ta; for(let i=0;i<8&&root.parentElement;i++) root=root.parentElement;
                       const img=root.querySelector('.swiper-slide-active img'); return img ? img.src : null; }"""
        )

    def select_candidate(self, src: str):
        """Make src the active slide and check it. 2026-11-09: a new candidate landed on the slide right of the active
        one, the click did not move the carousel, and two takes of a shot were made from the previous shot's frame.
        Now the slide is moved with Swiper's own slideTo and
        the active slide is read back; a mismatch stops the run before Create Video."""
        self.pause("select candidate image")
        self.page.evaluate(
            """src => { const img=[...document.querySelectorAll('img')].find(i=>i.src===src);
                       if(!img) throw new Error('candidate img vanished');
                       img.click(); }""",
            src,
        )
        # 2026-11-19 (three times in one short film): the wait in create_image saw one candidate, but a second one
        # landed after the pick and took the active slide, and the 5 s here ran out while it was still loading.
        # Now a late candidate is waited out (up to 90 s), and the pick counts only once it holds for 1 s.
        deadline, told = time.time() + 90, False
        while time.time() < deadline:
            self.page.wait_for_timeout(500)
            if any(self._is_gif(x) for x in self.modal_images()):   # never settle while a candidate is loading
                if not told:
                    self.log("a late candidate is still generating; waiting before selecting the picked frame")
                    told = True
                continue
            if self.active_frame() == src:
                self.page.wait_for_timeout(1000)
                if self.active_frame() == src and not any(self._is_gif(x) for x in self.modal_images()):
                    return src
                continue
            self.page.evaluate(
                """src => { const img=[...document.querySelectorAll('.swiper-slide img')].find(i=>i.src===src);
                           const sw=img && img.closest('.swiper'); if(!sw || !sw.swiper) return;
                           const slides=[...sw.querySelectorAll('.swiper-slide')];
                           sw.swiper.slideTo(slides.indexOf(img.closest('.swiper-slide'))); }""",
                src,
            )
        active = self.active_frame()
        new_here = active and (active in self._last_cands or active not in self._before_image)
        if self.auto_pick and new_here and not self._is_gif(active):
            # 2026-11-20 (twice in one 48-shot run): a late second candidate kept the active slide and slideTo
            # never moved it. Under --auto-pick any finished candidate is acceptable, so ship the active one
            # (the frame Create Video animates) instead of stopping the run. Only a frame that appeared after this
            # shot's Create Image counts: one left over from the previous shot (2026-11-09) still stops the run.
            self.log(f"auto-pick: the carousel kept {active[-40:]}; using it instead of {src[-40:]}")
            return active
        self.log(f"select_candidate: active {str(active)[-40:]} in this shot's candidates={active in self._last_cands}, "
                 f"present before Create Image={active in self._before_image}")
        self.shot_png("select_candidate_failed")
        raise RuntimeError(f"the dialog's active frame is {str(self.active_frame())[-40:]}, not the picked {src[-40:]}")

    def compare_image(self, label: str, files: list[Path]) -> Path | None:
        """images side by side, 800 px wide each, for a quick look (ve_qc.py prints its path)."""
        try:
            from PIL import Image
        except ImportError:
            return None
        if not files or not all(f.exists() for f in files):
            return None
        ims = [Image.open(f) for f in files]
        ims = [im.resize((800, round(im.height * 800 / im.width))) for im in ims]
        out = Image.new("RGB", (800 * len(ims), max(im.height for im in ims)), "white")
        for i, im in enumerate(ims):
            out.paste(im.convert("RGB"), (800 * i, 0))
        path = self.run_dir / f"{label}_compare.jpg"
        out.save(path, quality=90)
        return path

    # -- Start: chain (the previous shot's last frame becomes this shot's first frame)
    def wait_videos(self, uuids: list[str], timeout: float = 3600) -> dict[str, dict]:
        """block until every job is completed in My AI Videos; returns uuid -> library item."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            items = {x.get("uuid"): x for x in self.library(VID_CAT, "", 100)}
            bad = [u for u in uuids if u in items and re.search(r"fail|error|cancel", str(items[u].get("status")), re.I)]
            if bad:
                raise RuntimeError(f"previous video(s) failed: {bad}")
            done = {u: items[u] for u in uuids if u in items and items[u].get("status") == "completed"}
            if len(done) == len(uuids):
                return done
            self.log(f"waiting for the previous shot: {len(done)}/{len(uuids)} video(s) done")
            time.sleep(20)
        raise RuntimeError(f"previous video(s) not done within {timeout / 60:.0f} min")

    def download_video(self, item: dict, path: Path):
        body = self.page.request.get(APP_URL + f"library/download/{item['id']}", timeout=120_000).body()
        if body[4:8] != b"ftyp":
            raise RuntimeError(f"download of video {item['id']} is not an mp4")
        path.write_bytes(body)

    @staticmethod
    def last_frame(mp4: Path, jpg: Path):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.05", "-i", str(mp4), "-frames:v", "1", "-q:v", "2",
                        str(jpg)], check=True)

    def pick_take(self, label: str, frames: list[Path]) -> int:
        """with several takes of the previous shot, the human picks whose last frame to continue from."""
        if len(frames) == 1:
            return 0
        compare = self.compare_image(label, frames)
        self.log(f"QC {label}: {len(frames)} candidate(s)" + (f"; compare {compare}" if compare else ""))
        print(f"\n=== QC {label}: last frames of the previous shot's {len(frames)} takes ===")
        choices = "".join(str(i) for i in range(1, len(frames) + 1))
        a = self.ask(f"continue from take [{'/'.join(choices)}], q = quit: ", choices + "q")
        if a == "q":
            sys.exit("stopped at QC gate")
        return int(a) - 1

    def sidebar(self, name: str):
        self.page.evaluate(
            """t => { const els=[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&(e.innerText||'').trim()===t);
                if(!els.length) throw new Error('no sidebar item '+t); let el=els[els.length-1];
                for(let i=0;i<4&&el;i++){ if(el.tagName==='A'||el.tagName==='BUTTON'||el.getAttribute('data-target')) break; el=el.parentElement; }
                (el||els[0]).click(); }""", name)
        self.page.wait_for_timeout(2000)

    def open_folder(self, name: str):
        self.page.wait_for_function(
            "n => [...document.querySelectorAll('.library-folder-title')].some(e=>e.textContent.trim()===n&&e.getBoundingClientRect().width>0)",
            arg=name, timeout=20_000)
        self.page.evaluate("""n => [...document.querySelectorAll('.library-folder-title')]
                                .filter(e=>e.textContent.trim()===n&&e.getBoundingClientRect().width>0)[0].click()""", name)
        self.page.wait_for_timeout(3000)

    def library_items(self) -> list[dict]:
        return self.page.evaluate("""() => [...document.querySelectorAll('.library-item')].filter(e=>e.getBoundingClientRect().width>0)
            .map(e=>({id:e.getAttribute('data-ident'), text:(e.innerText||'').replace(/\\s+/g,' ').trim()}))""")

    def close_modal(self):
        """closing resets every option and both reference slots, so the slot bookkeeping is cleared too."""
        # the Close button is the nearest one above the prompt box: the first visible button.button-close eight levels up
        # left the dialog open (2026-11-16, three runs in a row); clicked again if the dialog is still there after 5 s
        for attempt in range(3):
            if not self.page.locator("#opt_prompt").is_visible():
                break
            hit = self.page.evaluate("""() => { const vis=e=>e.getBoundingClientRect().width>0;
                const tas=[...document.querySelectorAll('#opt_prompt')]; const ta=tas.find(vis);
                let root=ta, b=null;
                for(let i=0;i<8&&root.parentElement&&!b;i++){ root=root.parentElement;
                  b=[...root.querySelectorAll('button.button-close')].find(vis); }
                if(!b) throw new Error('dialog Close button not found'); b.click();
                return tas.length+' #opt_prompt, clicked '+b.className; }""")
            self.log(f"close dialog: {hit}")
            try:
                self.page.wait_for_selector("#opt_prompt", state="hidden", timeout=5_000)
            except PWTimeout:
                if attempt == 2:
                    self.shot_png("close_modal_stuck")
                    raise
                self.log("dialog still open after Close, clicking again")
        self.slot_ids, self.slot_srcs = [None, None], [None, None]

    def video_menu(self, item: dict, entry: str):
        """Media Library > My AI Videos > right-click the clip > menu entry (Voice Changer, Save Last Frame, ...)."""
        self.sidebar("Media Library")
        self.open_folder("My AI Videos")
        sel = f'.library-item[data-ident="{item["id"]}"]'
        for _ in range(30):  # older items sit behind "More" (each click adds about one page)
            if self.page.locator(sel).count():
                break
            more = self.page.locator("button:has-text('More'):visible")
            if not more.count():
                break
            more.first.evaluate("el => el.click()")
            self.page.wait_for_timeout(3000)
        if not self.page.locator(sel).count():
            raise RuntimeError(f"video {item['id']} not found in My AI Videos")
        self.page.locator(sel).first.scroll_into_view_if_needed()
        self.page.locator(sel).first.click(button="right")
        self.page.wait_for_timeout(1500)
        self.page.evaluate("""t => { const e=[...document.querySelectorAll('a')]
            .filter(e=>e.getBoundingClientRect().width>0&&(e.innerText||'').trim()===t).pop();
            if(!e) throw new Error('video menu has no '+t); e.click(); }""", entry)

    def save_last_frame(self, item: dict, title: str) -> int:
        """the clip's menu > Save Last Frame > Title (#modalFieldName) > Save: VE's own last frame (PNG 1920x1080) lands in
        My AI Images under that title (probed 2026-10-10). Returns its library id; replaces download -> ffmpeg -> upload."""
        before = {x["id"] for x in self.library(IMG_CAT, "", 30)}
        self.video_menu(item, "Save Last Frame")
        self.page.wait_for_selector("#modalFieldName", state="visible", timeout=15_000)
        self.page.fill("#modalFieldName", title)
        self.page.evaluate("""() => { const m=document.querySelector('#modalFieldName').closest('.bbm-modal')||document;
                                    const b=[...m.querySelectorAll('button.button-submit')].find(e=>e.getBoundingClientRect().width>0);
                                    if(!b) throw new Error('Save Last Frame: Save button not found'); b.click(); }""")
        for _ in range(24):
            time.sleep(5)
            new = [x for x in self.library(IMG_CAT, "", 30)
                   if x["id"] not in before and (x.get("name") or "").lower() == title.lower()]
            if len(new) == 1:
                self.log(f"last frame of video {item['id']} saved as library image {new[0]['id']} ({title})")
                self.sidebar("Create with AI")
                return int(new[0]["id"])
            if len(new) > 1:
                raise RuntimeError(f"several new images are named {title}: {[x['id'] for x in new]}")
        self.shot_png("save_last_frame_not_found")
        raise RuntimeError(f"Save Last Frame of video {item['id']} never appeared in My AI Images")

    def upload_file(self, path: Path, folder: str) -> int:
        """Media Library > folder > Upload file (a Dropzone) > Upload files; returns the new library id.
        VE capitalises the media name, so the new item is found by name case-insensitively."""
        # the upload dialog keeps sending to the folder of the page's first upload: a picture uploaded after narration audio
        # landed in Audio although Images was open (2026-11-16, three runs). Loading the page again resets it.
        if getattr(self, "uploaded_to", folder) != folder:
            self.log(f"reloading the page: the last upload went to {self.uploaded_to}, this one goes to {folder}")
            self.open_app()
        self.uploaded_to = folder
        self.sidebar("Media Library")
        self.open_folder(folder)
        before = {x["id"] for x in self.library_items()}
        self.page.evaluate("""() => { const b=[...document.querySelectorAll('button')].find(e=>/button-upload/.test(e.className)&&e.getBoundingClientRect().width>0);
                                    if(!b) throw new Error('no Upload file button'); b.click(); }""")
        self.page.wait_for_selector("input.dz-hidden-input", state="attached", timeout=15_000)
        self.page.set_input_files("input.dz-hidden-input", str(path))
        self.page.wait_for_timeout(2000)
        self.page.evaluate("""() => { const b=[...document.querySelectorAll('button')].find(e=>(e.innerText||'').trim()==='Upload files'&&e.getBoundingClientRect().width>0);
                                    if(!b) throw new Error('no Upload files button'); b.click(); }""")
        key = path.stem.lower()
        for _ in range(60):
            self.page.wait_for_timeout(3000)
            new = [x for x in self.library_items() if x["id"] not in before and key in x["text"].lower()]
            if len(new) == 1:
                self.log(f"uploaded {path.name} to {folder} as library item {new[0]['id']}")
                self.sidebar("Create with AI")
                return int(new[0]["id"])
            if len(new) > 1:
                raise RuntimeError(f"several new library items match {path.stem}: {new}")
        self.shot_png("upload_not_found")
        raise RuntimeError(f"uploaded {path.name} never appeared in {folder}")

    def use_from_library(self, lib_id: int, folder: str = "Images") -> str:
        """main dialog > Use from Library > folder > item > Choose: the image becomes the frame to animate."""
        before = set(self.all_modal_srcs())
        self.page.evaluate("() => document.querySelector('button.button-image-from-library').click()")
        self.open_folder(folder)
        sel = f'.library-item[data-ident="{lib_id}"]'
        self.page.wait_for_selector(sel, state="attached", timeout=15_000)
        self.page.locator(sel).first.evaluate("el => el.click()")
        self.page.wait_for_timeout(500)
        self.page.evaluate("""() => { const b=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Choose'&&b.getBoundingClientRect().width>0).pop();
                                    if(!b) throw new Error('Choose button not found'); b.click(); }""")
        for _ in range(20):
            self.page.wait_for_timeout(500)
            shown = [s for s in self.modal_images() if s not in before]
            if shown:
                self.log(f"library image {lib_id} is the frame")
                return shown[0]
        self.shot_png("use_from_library_failed")
        raise RuntimeError(f"library image {lib_id} did not show up in the dialog")

    def qc_gate(self, label: str, cands: list[str]) -> str | None:
        """Human QC: returns chosen src, None for re-roll, or SKIP (no video for this shot; the run goes on)."""
        for i, s in enumerate(cands, 1):
            try:
                data = self.page.request.get(s).body()
                (self.run_dir / f"{label}_cand{i}.jpg").write_bytes(data)
            except Exception as e:  # noqa: BLE001
                self.log(f"could not save candidate {i}: {e}")
        self.shot_png(f"{label}_candidates")
        compare = self.compare_image(label, [self.run_dir / f"{label}_cand{i}.jpg" for i in range(1, len(cands) + 1)])
        self.log(f"QC {label}: {len(cands)} candidate(s)" + (f"; compare {compare}" if compare else ""))
        print(f"\n=== QC {label}: {len(cands)} candidate(s) saved in {self.run_dir} ===")
        print("Look at the browser (or the saved jpgs). Does the frame match the scene?")
        choices = "".join(str(i) for i in range(1, len(cands) + 1))
        if self.auto_pick:
            self.log(f"QC {label}: auto-pick candidate 1")
            return cands[0]
        a = self.ask(f"pick [{'/'.join(choices)}], r = re-roll, s = skip this shot, q = quit: ", choices + "rsq")
        if a == "q":
            sys.exit("stopped at QC gate")
        if a == "s":
            return SKIP
        if a == "r":
            return None
        return cands[int(a) - 1]

    def set_duration(self, secs: int):
        self.set_checkbox("advanced_mode", True)
        self.set_checkbox("manual_video_length", True)
        self.pause(f"duration -> {secs}")
        self.page.evaluate(
            """v => { const r=document.querySelector('#opt_video_duration');
                     r.value=String(v);
                     r.dispatchEvent(new Event('input',{bubbles:true}));
                     r.dispatchEvent(new Event('change',{bubbles:true})); }""",
            secs,
        )
        got = self.page.input_value("#opt_video_duration")
        if int(float(got)) != secs:
            raise RuntimeError(f"duration slider shows {got}, wanted {secs}")
        self.log(f"duration {secs}s")

    def footer_uuid(self) -> str | None:
        """the dialog footer shows 'Video: <uuid>' for the last submitted job."""
        m = re.search(r"Video:\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
                      self.page.inner_text("body"))
        return m.group(1) if m else None

    def wait_for_slot(self):
        """block while MAX_IN_FLIGHT videos are processing on the account. The cap is per account, so jobs
        from another window count too. Only status 'completed' has been observed; anything else that is not
        a failure, created in the last 30 min, counts as busy (an old stuck item must not block forever)."""
        while True:
            now = time.time()
            busy = [x for x in self.library(VID_CAT, "", 100)
                    if x.get("status") != "completed" and not re.search(r"fail|error|cancel", str(x.get("status")), re.I)
                    and now - _utc(x["datetime"]) < 1800]
            if len(busy) < MAX_IN_FLIGHT:
                return
            self.log(f"{len(busy)} videos processing on the account (cap {MAX_IN_FLIGHT}); waiting 30 s")
            time.sleep(30)

    def confirm_submitted(self, before: str | None, i2v: str, t0: float) -> str:
        """the new job's uuid: the footer must change; then the library must hold it (over-cap jobs vanish)."""
        uuid = None
        for _ in range(20):
            self.page.wait_for_timeout(1000)
            u = self.footer_uuid()
            if u and u != before:
                uuid = u
                break
        if not uuid:  # fall back to the library: our prompt, created after the click
            head = i2v[:40]
            for x in self.library(VID_CAT, "", 20):
                created = _utc(x["datetime"])
                if (x.get("name") or "").startswith(head) and created >= t0 - 5:
                    uuid = x["uuid"]
                    break
        if not uuid:
            self.shot_png("submit_unconfirmed")
            raise RuntimeError(f"video submission not confirmed (alerts: {self.alerts()})")
        for _ in range(6):
            if any(x.get("uuid") == uuid for x in self.library(VID_CAT, "", 20)):
                return uuid
            time.sleep(5)
        raise Dropped(f"video {uuid} never appeared in My AI Videos (dropped by the {MAX_IN_FLIGHT}-job cap?)", uuid)

    def create_video_plain(self, i2v: str, enhance_video: bool, speech: bool = False):
        """the normal path. A shot without a spoken line is silent (Video Only: sound is added in post); a shot with one
        keeps VE's sound, so the line written in the prompt is spoken, at the shot's own length."""
        self.set_checkbox("talking_video", False)
        self.set_checkbox("narration_video", False)
        self.set_checkbox("video_only", not speech)
        self.set_checkbox("enhance_video_prompt", enhance_video)
        self.fill("#opt_video_prompt", i2v)
        btn = self.page.locator("button.button-generate-video-submit")
        if btn.count():
            self.pause("click Create Video")
            btn.first.evaluate("el => el.click()")
        else:
            self.dom_click("button:has-text('Create Video')")
        self.log(f"Create Video sent ({'plain, with speech' if speech else 'plain'})")

    def create_video_lipsync(self, i2v: str, speech: list[tuple[int, str]]):
        """Lipsync HD: ticking it disables the main video prompt and turns Create Video into
        button-generate-talking-video, which opens "Create Lipsync Audio" (probed 2026-10-09/10): its own Video Prompt
        (a second textarea[name=prompt]; VE's placeholder defines who is Actor 1 / Actor 2 there), Actor 1 Script
        (#opt_prompt_actor1), Add Actor 2 -> Actor 2 Script (#opt_prompt_actor2), and Create.
        One line: Actor 1 Script. Two lines: each actor's line goes to that actor's script."""
        scripts = {1: speech[0][1], 2: ""} if len(speech) == 1 else dict(speech)
        self.set_checkbox("narration_video", False)
        self.set_checkbox("video_only", False)  # the lipsync clip carries the spoken line
        self.set_checkbox("talking_video", True)
        self.page.wait_for_timeout(500)
        self.pause("click Create Video (lipsync)")
        self.page.evaluate("""() => { const b=[...document.querySelectorAll('button.button-generate-talking-video')].find(e=>e.getBoundingClientRect().width>0);
                                    if(!b) throw new Error('lipsync Create Video button not found'); b.click(); }""")
        try:
            self.page.wait_for_selector("#opt_prompt_actor1", state="visible", timeout=15_000)
        except PWTimeout:
            self.shot_png("lipsync_dialog_missing")
            raise RuntimeError("Create Lipsync Audio dialog did not open")
        # this Video Prompt reuses id="opt_prompt" (same as the main image prompt), so find it by its placeholder
        self.page.evaluate("""() => { const t=[...document.querySelectorAll('textarea[name=prompt]')]
                                      .find(e=>e.getBoundingClientRect().width>0&&!e.disabled&&/Actor 1 is/.test(e.placeholder||''));
                                    if(!t) throw new Error('lipsync Video Prompt not found'); t.setAttribute('data-ve','lipsync-prompt'); }""")
        if scripts[2] and not self.page.locator("#opt_prompt_actor2").is_visible():
            self.page.evaluate("""() => { const b=[...document.querySelectorAll('button,a')].find(e=>/Add Actor 2/.test(e.innerText||'')&&e.getBoundingClientRect().width>0);
                                        if(!b) throw new Error('Add Actor 2 not found'); b.click(); }""")
            self.page.wait_for_selector("#opt_prompt_actor2", state="visible", timeout=5_000)
        self.page.locator('textarea[data-ve="lipsync-prompt"]').fill(i2v)
        self.page.locator("#opt_prompt_actor1").fill(scripts[1])
        a2 = self.page.locator("#opt_prompt_actor2")
        if a2.is_visible():  # a second script left over from an earlier shot would make VE add a second speaker
            a2.fill(scripts[2])
        got = (self.page.locator('textarea[data-ve="lipsync-prompt"]').input_value(), self.page.input_value("#opt_prompt_actor1"),
               a2.input_value() if a2.is_visible() else "")
        if got != (i2v, scripts[1], scripts[2]):
            self.shot_png("lipsync_fill_failed")
            raise RuntimeError("lipsync Video Prompt / Actor Scripts did not take the text")
        self.pause("submit lipsync video")
        self.page.evaluate("""() => { const m=document.querySelector('#opt_prompt_actor1').closest('.modal')||document;
                                    const b=[...m.querySelectorAll('button')].find(e=>e.innerText.trim()==='Create'&&e.getBoundingClientRect().width>0);
                                    if(!b) throw new Error('lipsync Create button not found'); b.click(); }""")
        self.log("Create Video sent (lipsync): " + " / ".join(f'Actor {k}: "{v}"' for k, v in scripts.items() if v))

    def create_video_narration(self, i2v: str, audio_id: int, enhance_video: bool):
        """Narration Video (probed 2026-10-18): with narration_video ticked the visible Create Video is the talking-video
        button, which opens "Create Narration Video - Create Audio" (tabs Text to Speech / CloneVoice.ai / Voice Recording /
        Import Audio). Import Audio > select opens the Media Library picker; the audio is capped at 10 s. Then
        Create Narration Video submits. Tabs switch only on a real mouse click, not on a DOM click()."""
        self.set_checkbox("talking_video", False)
        self.set_checkbox("narration_video", True)
        # the official narration workflows keep Advanced Mode off: the clip length follows the audio
        self.set_checkbox("advanced_mode", False)
        if self.page.locator("input[name=video_only]").count():
            self.set_checkbox("video_only", False)
        if self.page.locator("input[name=enhance_video_prompt]").count():
            self.set_checkbox("enhance_video_prompt", enhance_video)
        self.fill("#opt_video_prompt", i2v)
        self.pause("click Create Video (narration)")
        self.page.evaluate("""() => { const b=[...document.querySelectorAll('button.button-generate-talking-video')].find(e=>e.getBoundingClientRect().width>0);
                                    if(!b) throw new Error('narration Create Video button not found'); b.click(); }""")
        try:
            self.page.wait_for_selector("text=Create Narration Video - Create Audio", state="visible", timeout=15_000)
        except PWTimeout:
            self.shot_png("narration_dialog_missing")
            raise RuntimeError(f"Create Narration Video dialog did not open (alerts: {self.alerts()})")
        self.page.locator("a:visible:text-is('Import Audio')").first.click()
        self.page.locator("button.button-select-file:visible").first.click()
        self.open_folder("Audio")
        sel = f'.library-item[data-ident="{audio_id}"]'
        self.page.wait_for_selector(sel, state="attached", timeout=15_000)
        self.page.locator(sel).first.evaluate("el => el.click()")
        self.page.wait_for_timeout(500)
        self.page.evaluate("""() => { const b=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Choose'&&b.getBoundingClientRect().width>0).pop();
                                    if(!b) throw new Error('Choose button not found'); b.click(); }""")
        self.page.wait_for_timeout(2000)
        self.shot_png("narration_audio_chosen")
        self.pause("click Create Narration Video")
        self.page.locator("button:visible:text-is('Create Narration Video')").first.click()
        self.log(f"Create Video sent (narration, audio library item {audio_id})")

    def inspect(self):
        dump = self.page.evaluate(
            """() => {
              const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0};
              return [...document.querySelectorAll('input,select,textarea,button')].map(e=>({
                tag:e.tagName, type:e.type||'', id:e.id, name:e.name,
                cls:(e.className||'').toString().slice(0,60),
                text:(e.textContent||'').trim().slice(0,40),
                checked:e.type==='checkbox'?e.checked:undefined,
                options:e.tagName==='SELECT'?[...e.options].map(o=>o.value):undefined,
                visible:vis(e)}));
            }"""
        )
        out = self.run_dir / "inspect.json"
        out.write_text(json.dumps(dump, indent=1, ensure_ascii=False))
        for d in dump:
            if d["visible"]:
                print(d["tag"], d["type"], d["id"], d["name"], d["cls"], d["text"], d.get("checked", ""))
        self.log(f"full dump -> {out}")


# ---------------------------------------------------------------- orchestration


def new_run_dir(base: Path, prefix: str = "") -> Path:
    """base/<prefix><timestamp>/ for one run; base defaults to tools/ve-runner/runs, --run-dir puts it in the film's folder."""
    run_dir = base / time.strftime(f"{prefix}%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True)
    return run_dir


def run(args):
    run_dir = new_run_dir(Path(args.run_dir).expanduser().resolve() if args.run_dir else HERE / "runs")
    print(f"run dir: {run_dir}", flush=True)  # ve_qc.py and ve_collect.py take this path
    # run.log is what ve_qc.py and a human watch (stdout is often redirected), so a crash or an early exit
    # must land there too, not only on stdout
    try:
        _run(args, run_dir)
    except SystemExit as e:
        if e.code not in (0, None):
            with (run_dir / "run.log").open("a") as f:
                f.write(f"{time.strftime('%H:%M:%S')} stopped: {e.code}\n")
        raise
    except BaseException:
        with (run_dir / "run.log").open("a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} crashed:\n{traceback.format_exc()}")
        raise


def _run(args, run_dir: Path):
    rs = None if args.inspect or args.login else parse_runsheet(Path(args.runsheet))
    if rs:  # the dialog refuses audio over 10 s: fail before the browser opens, not mid-run
        for s in rs.shots:
            if s.speech and not s.narration and not args.speech_in_prompt:
                _check_lipsync(s.n, s.speech)
            if s.narration and (sec := audio_seconds(s.narration)) > NARRATION_MAX:
                sys.exit(f"shot {s.n}: narration {Path(s.narration).name} is {sec:.2f} s, over VE's {NARRATION_MAX:.0f} s cap")

    if not HEADED and never_logged_in(HERE / ".profile"):   # headless would only sit 90 s on a login page nobody can see
        sys.exit("✗ " + LOGIN_HINT.format(profile=HERE / ".profile"))
    with sync_playwright() as pw:
        ctx = launch_browser(pw, HERE / ".profile")
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        ve = VE(page, run_dir, args.step, args.auto_pick, args.aspect)
        ve.ref_folder = args.ref_folder
        ve.open_app()
        if args.login:   # only the login: the editor is up, so the profile now holds it
            ve.log("logged in; the profile keeps it for later runs")
            ctx.close()
            return
        # narration audio goes to Media Library > Audio before the dialog opens: the upload uses the sidebar
        narration_ids: dict[str, int] = {}
        if rs:
            wanted_n = set(args.shots) if args.shots else {s.n for s in rs.shots}
            for s in rs.shots:
                if s.n in wanted_n and s.narration and s.narration not in narration_ids:
                    narration_ids[s.narration] = ve.upload_file(Path(s.narration), "Audio")
            if narration_ids:
                (run_dir / "narration.json").write_text(json.dumps(narration_ids, indent=1, ensure_ascii=False))
        ve.open_modal()

        if args.inspect:
            ve.inspect()
            if wait_for_enter(HEADED, sys.stdin.isatty()):
                input("Modal is open. Press Enter to close the browser. ")
            ctx.close()
            return

        wanted = set(args.shots) if args.shots else {s.n for s in rs.shots}
        todo = [s for s in rs.shots if s.n in wanted]
        if todo and todo[0].start in ("chain", "same"):  # fail before spending anything, not mid-run
            sys.exit(f"shot {todo[0].n}: Start '{todo[0].start}' needs a previous shot in this run")
        image_type = args.image_type
        # The dialog resets every option and both reference slots whenever it reopens, and with
        # Use Consistent Character on but an empty slot VE refuses Create Image ("Please select a
        # reference photo."). So the dialog stays open for the whole run; slots are picked once.

        # ---- character masters: one single-actor reference per actor, saved in My AI Images
        masters: dict[str, int] = {k: int(v) for k, v in json.loads(Path(args.masters).read_text()).items()} if args.masters else {}
        needed = sorted({a for s in todo for a in s.cast}) if not args.no_cc else []
        for name in needed:
            if name in masters:
                continue
            idx = int(name.split()[1])
            if idx > len(rs.actors):
                sys.exit(f"{name} is cast but the run sheet has only {len(rs.actors)} actor line(s)")
            ve.ensure_cast([])
            label = f"master{idx}"
            while True:
                cands = ve.create_image(rs.actors[idx - 1], image_type, enhance=args.hero_enhance,
                                        creative=args.creative)
                pick = ve.qc_gate(label, cands)
                if pick:
                    break
                ve.log(f"{label} re-roll")
            pick = ve.select_candidate(pick)
            (run_dir / f"{label}.jpg").write_bytes(page.request.get(pick).body())
            masters[name] = ve.save_to_library(pick, rs.actors[idx - 1])["id"]
            (run_dir / "masters.json").write_text(json.dumps(masters, indent=1))
            ve.log(f"{name} master = library image {masters[name]}")
        if masters:
            (run_dir / "masters.json").write_text(json.dumps(masters, indent=1))

        # ---- shots
        submitted: list[dict] = []
        saved: dict[str, int] = {}  # Save: master shots -> My AI Images id
        takes_of: dict[int, list[str]] = {}  # shot number -> its video uuids, for a following chain shot
        for i, shot in enumerate(todo):
            label = f"shot{shot.n}"
            cast_ids = [] if args.no_cc else [masters[a] for a in shot.cast]
            if shot.start == "chain":
                # the previous shot's videos must be finished; with several takes the human picks whose last frame to
                # continue from (frames downloaded only for that comparison). VE's Save Last Frame puts the chosen take's
                # last frame in My AI Images, and Use from Library makes it the frame to animate.
                # No image is generated, so Consistent Character stays off for this shot.
                prev = todo[i - 1]
                uuids = takes_of[prev.n]
                done = ve.wait_videos(uuids)
                k = 0
                if len(uuids) > 1:
                    frames = []
                    for t, u in enumerate(uuids, 1):
                        mp4, jpg = run_dir / f"{label}_prev_t{t}.mp4", run_dir / f"{label}_prev_t{t}_last.jpg"
                        ve.download_video(done[u], mp4)
                        ve.last_frame(mp4, jpg)
                        frames.append(jpg)
                    k = ve.pick_take(f"{label}_chain", frames)
                ve.close_modal()
                lib_id = ve.save_last_frame(done[uuids[k]], f"chain_{run_dir.name}_{label}")
                ve.open_modal()
                ve.set_duration(shot.duration)
                ve.ensure_cast([])
                pick = ve.use_from_library(lib_id, "My AI Images")
                ve.log(f"{label} continues from shot{prev.n} take {k + 1}")
            elif shot.start == "image":
                # the upload happens in Media Library, so the dialog closes first (closing resets options and slots)
                ve.close_modal()
                lib_id = ve.upload_file(Path(shot.start_image), "Images")
                ve.open_modal()
                ve.set_duration(shot.duration)
                ve.ensure_cast([])
                pick = ve.use_from_library(lib_id, "Images")
                ve.log(f"{label} animates {Path(shot.start_image).name} (library image {lib_id})")
            elif shot.start == "same":
                # the previous shot's frame is still the selected candidate in the open dialog (--takes relies on
                # the same thing), so only the duration and the video prompt change: an A/B test on one first frame
                ve.set_duration(shot.duration)
                ve.log(f"{label} reuses shot{todo[i - 1].n}'s first frame")
            else:
                ve.open_modal()  # no-op while the dialog is still open
                if not shot.narration:  # a narrated clip takes its length from the audio (Advanced Mode off)
                    ve.set_duration(shot.duration)  # BEFORE lipsync: ticking it hides the slider
                while True:
                    ve.ensure_cast(cast_ids)  # verify the slots before every Create Image
                    ve.wait_for_slot()  # images wait behind the account cap too: with 5 videos processing, Create Image sat 4 min with no candidate (2026-10-24)
                    try:
                        cands = ve.create_image(shot.t2i, image_type, enhance=False, creative=args.creative)
                    except NoCandidates as e:
                        ve.log(f"{label}: {e}; retrying once when a slot is free")
                        ve.wait_for_slot()
                        cands = ve.create_image(shot.t2i, image_type, enhance=False, creative=args.creative)
                    pick = ve.qc_gate(label, cands)
                    if pick:
                        break
                    ve.log(f"{label} re-roll")
                if pick is SKIP:
                    ve.log(f"{label} skipped at QC (no video)")
                    continue
            pick = ve.select_candidate(pick)
            (run_dir / f"{label}_frame.jpg").write_bytes(page.request.get(pick).body())
            if shot.save == "master":
                saved[label] = ve.save_to_library(pick, shot.t2i)["id"]
                (run_dir / "saved.json").write_text(json.dumps(saved, indent=1))
                ve.log(f"{label} saved as library image {saved[label]}; no video (Save: master)")
                continue
            # --takes N: N videos from the same first frame, to pick one (a standing single puppet
            # turns toward the camera in most takes whatever the prompt; picking is the remedy)
            for take in range(1, args.takes + 1):
                tlabel = label if args.takes == 1 else f"{label}_t{take}"
                for attempt in (1, 2):  # a job dropped by the account-wide cap is resubmitted once
                    ve.wait_for_slot()
                    ve.set_checkbox("shared", False)
                    before, t0 = ve.footer_uuid(), time.time()
                    if shot.narration:
                        ve.create_video_narration(shot.i2v, narration_ids[shot.narration], args.video_enhance)
                    elif shot.dialogue and not args.speech_in_prompt:
                        ve.create_video_lipsync(shot.i2v, shot.speech)
                    else:
                        ve.create_video_plain(shot.i2v, args.video_enhance, speech=bool(shot.dialogue) or args.with_sound)
                    try:
                        uuid = ve.confirm_submitted(before, shot.i2v, t0)
                        break
                    except Dropped as e:
                        if shot.narration and e.uuid:
                            # narrated clips landed in My AI Videos in the one live test; until that holds across runs,
                            # keep the uuid instead of resubmitting, so one shot never costs two generations
                            uuid = e.uuid
                            ve.log(f"{tlabel}: {e}; kept {uuid} unconfirmed (narration), not resubmitted")
                            break
                        if attempt == 2:
                            raise
                        ve.log(f"{tlabel}: {e}; resubmitting once when a slot is free")
                takes_of.setdefault(shot.n, []).append(uuid)
                submitted.append({"label": tlabel, "video_uuid": uuid, "cast": shot.cast, "duration": shot.duration,
                                  "submitted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))})
                (run_dir / "submitted.json").write_text(json.dumps(submitted, indent=1, ensure_ascii=False))
                ve.shot_png(f"{tlabel}_submitted")
                ve.log(f"{tlabel} submitted as {uuid} ({shot.duration}s, cast {shot.cast or 'none'}, "
                       f"{'narration' if shot.narration else 'with speech' if shot.dialogue and args.speech_in_prompt else 'lipsync' if shot.dialogue else 'with sound' if args.with_sound else 'plain'})")

        # ve_qc.py detects the end by "all N shot(s) submitted": keep that phrase in both cases
        if submitted:
            ve.log(f"all {len(submitted)} shot(s) submitted. Collect the clips with:\n"
                   f"  python3 ve_collect.py --submitted {run_dir / 'submitted.json'} --out <dir>")
        else:
            ve.log(f"all 0 shot(s) submitted (no video); saved images: {saved}")
        if wait_for_enter(HEADED, sys.stdin.isatty()):
            input("Done. Press Enter to close the browser. ")
        ctx.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runsheet", nargs="?", help="markdown run sheet / storyboard")
    ap.add_argument("--shots", type=int, nargs="*", help="only these shot numbers")
    ap.add_argument("--run-dir", help="parent folder for this run's <timestamp>/ folder, e.g. projects/<film>/ve-runs "
                    "(default: tools/ve-runner/runs)")
    ap.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"],
                    help="the dialog's frame shape for images and videos (default 16:9; 9:16 for vertical shorts)")
    ap.add_argument("--ref-folder", default="My AI Images",
                    help="Media Library folder the --masters ids live in (Images: photos uploaded by hand)")
    ap.add_argument("--masters", help='JSON {"Actor 1": <library id in --ref-folder>, ...} from an earlier run or an upload: skip those masters')
    ap.add_argument("--hero-enhance", action="store_true",
                    help="let VE rewrite the master prompts (default OFF: it translates and dilutes style wording)")
    ap.add_argument("--creative", action="store_true", help="Use Creative mode for images (default OFF)")
    ap.add_argument("--no-cc", action="store_true", help="Consistent Character OFF: no masters, no reference slots")
    ap.add_argument("--image-type", default="photorealistic",
                    choices=["human", "2d", "3d", "photorealistic", "other"])
    ap.add_argument("--speech-in-prompt", action="store_true",
                    help="shots with a spoken line take the normal path with sound (the line spoken from the video prompt, at "
                         "the shot's own length) instead of Lipsync HD. Tested 2026-10-09: length and pace follow the "
                         "settings, but puppets moved more and the line was burned in as a caption; Lipsync HD stayed clean. "
                         "Retested 2026-11-08 (photorealistic, 4 shots, 24 clips): the captions came from 'No subtitles' in the "
                         "prompt (9/10 with it, 0/14 without); lengths matched; written as one line the speech starts 2.5-4.5 s in, written as timed beats ([ACTION 0-2s] WHO says '...'; "
                         "drama_sheet.py --speech-in-prompt) it started at 0.0-1.6 s in 11 of 12 clips")
    ap.add_argument("--with-sound", action="store_true",
                    help="keep VE's sound on shots without a spoken line too (Video Only off), so [PRODUCTION SOUND] in the "
                         "video prompt becomes ambience; default: silent clips, sound added in post")
    ap.add_argument("--takes", type=int, default=1,
                    help="videos per shot from the same first frame, to pick one (default 1, max 5)")
    ap.add_argument("--video-enhance", action="store_true",
                    help="let VE rewrite the video prompt (default: paste verbatim)")
    ap.add_argument("--auto-pick", action="store_true",
                    help="accept candidate 1 at every image QC gate without asking (the chain-take gate still asks); "
                         "check the saved candidates afterwards and re-run a broken shot with --shots")
    ap.add_argument("--step", action="store_true", help="confirm before every click")
    ap.add_argument("--inspect", action="store_true", help="dump modal DOM and exit")
    ap.add_argument("--login", action="store_true",
                    help="open the editor, wait for the user to log in (with S2F_VE_HEADED=1: a window, up to 10 minutes), then close")
    ap.add_argument("--skip-checklist", help="run even though the start checklist (tools/checklist) fails for this episode: give the "
                         "reason, it is logged in <episode>/nightly/checklist_skips.jsonl")
    args = ap.parse_args()
    if not args.inspect and not args.login and not args.runsheet:
        ap.error("runsheet path required (or --inspect / --login)")
    if not 1 <= args.takes <= MAX_IN_FLIGHT:
        ap.error(f"--takes must be 1..{MAX_IN_FLIGHT}")
    if args.runsheet:   # a run sheet inside an episode folder (doc.json / day.json): the start checklist must pass before
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "checklist"))   # anything is submitted; elsewhere it does not apply
        import checklist
        checklist.gate(args.runsheet, "start", args.skip_checklist, "ve")
    run(args)


if __name__ == "__main__":
    main()
