#!/usr/bin/env python3
"""Generate sound effects with VideoExpress AI Sound Maker (Sound From Prompt) on your own account, from a list of
prompts, into your user asset layer ($S2F_ASSETS_LOCAL/sfx/ve-gen/, entries in $S2F_ASSETS_LOCAL/sfx/manifest.json).

  python3 tools/assets/gen_sfx_ve.py <prompts.json> [--dry-run] [--only <id>] [--yes] [--skip-checklist "<reason>"]

prompts.json is a list of {"id", "prompt", "tags", "tags_zh"} and an optional "duration" (whole seconds, 2-7, default
5). Example: tools/assets/sfx_prompts.example.json. Write the prompt in short plain English and end it with "no music,
no voice" (skills/ve-director/rules/04-platform-videoexpress.md: a Chinese prompt gave the wrong sounds).
An id is lower-case letters, digits and "-"; the sound is saved as ve-gen/<id>.mp3 and its manifest entry has that id.
An id already in the user manifest with its file on disk is skipped, so a stopped run can be started again. A job
VideoExpress has accepted is written to $S2F_ASSETS_LOCAL/sfx/ve-gen-log/pending.json at once; if the run stops before
its download, the next run downloads that job instead of paying for the prompt again. A sound
with the same id as a bundled one (assets/sfx) replaces it for doc_sfx.py; list a new id in a kind's "files" in
skills/ve-director/doc/sfx_map.json (or a script's own doc.json "sfx_map") to use it.

Every sound uses VideoExpress credits. Without --yes the script prints how many it will make and asks first (in a
terminal; elsewhere it stops and asks for --yes). --dry-run only prints the plan and opens no browser.
The browser is the one tools/ve-runner uses: Chrome on the persistent profile tools/ve-runner/.profile (--profile to
use another), headless unless S2F_VE_HEADED=1. Log in once there with
  S2F_VE_HEADED=1 python3 tools/ve-runner/ve_runner.py --login
This script never types a password; if the editor does not open (login expired) it stops.
Like ve_runner.py, it runs the start checklist (tools/checklist) when the prompts file sits in an episode folder.

How it drives the page (checked 2026-11-17 with one sound): the "AI Sound Maker" card in Create with AI opens a dialog;
the visible textarea #opt_prompt takes the prompt, the range #opt_audio_duration the length, and the visible
"Create Sound" button (.button-submit-create-sound) sends POST /ai/api/create_sound (prompt, duration), which answers
{"success": true, "uuid": ...}. The sound is ready about 25 s later at
https://s3.renderplatform.com/user-assets/preview/generated_audio/<uuid>.mp3, which this script downloads. It does not
press "Save Sound", so nothing is added to your VideoExpress media library.
Checked live (2026-11-17, headless, four sounds in all): one run of this script with three prompts of 3, 5 and 7 s
pressed Create Sound itself for each one in turn, in the same dialog, and saved all three (about 22 s per sound); each
file measured exactly the length asked for (ffprobe 3.0 / 5.0 / 7.0 s; mp3, 16 kHz mono; not silent, mean volume about
-32 dB), the requests carried the length (no warning was logged), and the manifest entries are complete. Running the
same command again skipped all three and opened no browser. A fourth prompt (4 s) was killed right after its Create
Sound answer: the next run downloaded that job from pending.json without pressing Create Sound again, and emptied
pending.json. The script logs a warning when a request does not carry the duration.
"""
from __future__ import annotations

import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()

import argparse
import datetime
import json
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VE_RUNNER = REPO / "tools/ve-runner"
SUBDIR = "ve-gen"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")
DURATIONS = range(2, 8)       # the dialog's slider: 2-7 s
DEFAULT_DURATION = 5
SOURCE = "VideoExpress AI Sound Maker (Sound From Prompt), generated with the user's own account"
# must contain "VideoExpress": doc_sfx.LICENSED accepts it (tests/test_gen_sfx_ve.py checks this)
LICENSE = "VideoExpress: under the plan of the account that generated it"
PREVIEW_URL = "https://s3.renderplatform.com/user-assets/preview/generated_audio/{uuid}.mp3"
CREATE_API = "/ai/api/create_sound"
READY_TIMEOUT = 240           # seconds to wait for one sound
POLL = 5


class PromptError(ValueError):
    pass


# ---------------------------------------------------------------- pure logic (tested in tests/test_gen_sfx_ve.py)
def parse_prompts(data) -> list[dict]:
    """Check a prompts list and return it with "duration" filled in. Stops on the first problem with what to fix."""
    if not isinstance(data, list) or not data:
        raise PromptError("the prompts file must be a non-empty JSON list of {id, prompt, tags, tags_zh}")
    out, seen = [], set()
    for n, x in enumerate(data, 1):
        if not isinstance(x, dict):
            raise PromptError(f"item {n}: must be an object")
        i = x.get("id")
        if not isinstance(i, str) or not ID_RE.match(i):
            raise PromptError(f"item {n}: id {i!r} must be lower-case letters, digits and '-' (at most 60)")
        if i in seen:
            raise PromptError(f"item {n}: id {i!r} appears twice")
        seen.add(i)
        p = x.get("prompt")
        if not isinstance(p, str) or not p.strip():
            raise PromptError(f"{i}: prompt is empty")
        for k in ("tags", "tags_zh"):
            v = x.get(k, [])
            if not isinstance(v, list) or not all(isinstance(t, str) for t in v):
                raise PromptError(f"{i}: {k} must be a list of strings")
        d = x.get("duration", DEFAULT_DURATION)
        if not isinstance(d, int) or isinstance(d, bool) or d not in DURATIONS:
            raise PromptError(f"{i}: duration must be a whole number of seconds from 2 to 7, got {d!r}")
        out.append({"id": i, "prompt": p.strip(), "tags": list(x.get("tags", [])), "tags_zh": list(x.get("tags_zh", [])),
                    "duration": d})
    return out


def file_for(sid: str) -> str:
    """The manifest "file" of a sound, relative to the layer's sfx/ folder."""
    return f"{SUBDIR}/{sid}.mp3"


def select(prompts: list[dict], only: list[str] | None) -> list[dict]:
    """The prompts named by --only (all when None); an unknown id stops."""
    if not only:
        return prompts
    known = {p["id"] for p in prompts}
    bad = [i for i in only if i not in known]
    if bad:
        raise PromptError(f"--only: not in the prompts file: {', '.join(bad)}")
    return [p for p in prompts if p["id"] in only]


def split_done(prompts: list[dict], manifest: list[dict], sfx_dir: Path | None) -> tuple[list[dict], list[dict]]:
    """(to make, already made): made = its id is in the manifest and that entry's file is on disk."""
    have = {m["id"]: m for m in manifest}
    todo, done = [], []
    for p in prompts:
        m = have.get(p["id"])
        (done if m and sfx_dir is not None and (sfx_dir / m["file"]).is_file() else todo).append(p)
    return todo, done


def make_entry(p: dict, uuid: str, day: str, seconds: float | None = None) -> dict:
    """The manifest entry for a generated sound (same fields as assets/sfx/manifest.json)."""
    return {"id": p["id"], "file": file_for(p["id"]), "query": p["prompt"], "tags": p["tags"], "tags_zh": p["tags_zh"],
            "source": SOURCE, "license": LICENSE, "author": "", "source_url": PREVIEW_URL.format(uuid=uuid),
            "duration_hint": round(seconds, 2) if seconds else p["duration"], "downloaded_at": day}


def merge(manifest: list[dict], entry: dict) -> list[dict]:
    """manifest with entry added; it replaces an entry of the same id in place."""
    out, put = [], False
    for m in manifest:
        if m["id"] == entry["id"]:
            out.append(entry)
            put = True
        else:
            out.append(m)
    return out if put else out + [entry]


def plan_lines(todo: list[dict], done: list[dict], sfx_dir: Path | None, pending: dict | None = None) -> list[str]:
    pending = pending or {}
    where = str(sfx_dir) if sfx_dir else "(S2F_ASSETS_LOCAL is not set: set it to your user layer folder)"
    new = [p for p in todo if p["id"] not in pending]
    lines = [f"user layer: {where}",
             f"to generate: {len(new)} sound(s); each one uses VideoExpress credits",
             f"already there (skipped): {len(done)}" + (f": {', '.join(p['id'] for p in done)}" if done else "")]
    if len(new) < len(todo):
        lines.append(f"sent earlier, only downloaded now (no credits): {', '.join(p['id'] for p in todo if p['id'] in pending)}")
    lines += [f"  {p['id']:<24} {p['duration']} s  {file_for(p['id'])}  \"{p['prompt']}\""
              + ("  (earlier job)" if p["id"] in pending else "") for p in todo]
    return lines


def with_pending(pending: dict, sid: str, uuid: str | None) -> dict:
    """The record of jobs sent but not yet saved ({id: uuid}): a uuid adds sid, None removes it. A job is written
    down as soon as VideoExpress answers, so a run stopped before the download fetches it later without paying again."""
    out = {k: v for k, v in pending.items() if k != sid}
    if uuid:
        out[sid] = uuid
    return out


def read_pending(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_pending(path: Path, pending: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pending, indent=1) + "\n", encoding="utf-8")


def read_manifest(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def write_manifest(path: Path, manifest: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)


def confirm(n: int, yes: bool, isatty: bool, ask=input) -> bool:
    """Go ahead? --yes: yes. In a terminal: ask. Elsewhere (an agent, a pipe): no, the caller says to add --yes."""
    if yes or n == 0:
        return True
    if not isatty:
        return False
    return ask(f"Generate {n} sound(s) with VideoExpress? Each uses credits. [y/N] ").strip().lower() in ("y", "yes")


# ---------------------------------------------------------------- browser
def audio_seconds(path: Path) -> float | None:
    import subprocess
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, check=True)
        return float(r.stdout.strip())
    except (OSError, ValueError, subprocess.CalledProcessError):
        return None


class SoundMaker:
    """The AI Sound Maker dialog, opened once and reused for every prompt."""

    def __init__(self, ve, log):
        self.ve, self.page, self.log = ve, ve.page, log

    def open(self):
        self.ve.dismiss_news()
        self.page.evaluate(
            """() => {
              const h = [...document.querySelectorAll('h3')].find(h => h.textContent.trim() === 'AI Sound Maker');
              if (!h) throw new Error('AI Sound Maker card not found');
              h.scrollIntoView();
              for (let e = h.parentElement; e; e = e.parentElement) {
                const b = e.querySelector('button.btn-circle-big'); if (b) { b.click(); return; } }
              throw new Error('AI Sound Maker card button not found');
            }""")
        self.page.locator("button.button-submit-create-sound:visible").first.wait_for(timeout=15_000)
        self.log("AI Sound Maker open")

    def set_duration(self, d: int):
        r = self.page.locator("input#opt_audio_duration:visible").first
        if r.input_value() != str(d):
            r.evaluate("(el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles: true}));"
                       " el.dispatchEvent(new Event('change', {bubbles: true})); }", str(d))
        if r.input_value() != str(d):
            raise RuntimeError(f"duration slider refused {d}")

    def create(self, p: dict) -> str:
        """Fill the prompt, press Create Sound once, return the job uuid from the create_sound answer."""
        self.ve.dismiss_news()
        ta = self.page.locator("textarea#opt_prompt:visible").first
        ta.fill(p["prompt"])
        if ta.input_value() != p["prompt"]:
            raise RuntimeError("the prompt box did not take the text")
        self.set_duration(p["duration"])
        with self.page.expect_response(lambda r: CREATE_API in r.url and r.request.method == "POST", timeout=60_000) as info:
            self.page.locator("button.button-submit-create-sound:visible").first.evaluate("el => el.click()")
        resp = info.value
        sent = resp.request.post_data or ""
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001
            body = {}
        if not body.get("success") or not body.get("uuid"):
            alerts = self.ve.alerts()
            raise RuntimeError(f"Create Sound was refused: {str(body)[:200]} {alerts[-2:] if alerts else ''}")
        if f"duration={p['duration']}" not in sent:
            self.log(f"warning: the request did not carry duration={p['duration']} ({sent[:120]})")
        return body["uuid"]

    def download(self, uuid: str, dest: Path) -> None:
        url = PREVIEW_URL.format(uuid=uuid)
        t0 = time.time()
        while time.time() - t0 < READY_TIMEOUT:
            time.sleep(POLL)
            try:
                r = self.page.request.get(url, timeout=30_000)
            except Exception:  # noqa: BLE001  transient network error: try again
                continue
            if r.ok:
                data = r.body()
                if len(data) > 1000:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    tmp = dest.with_suffix(".part")
                    tmp.write_bytes(data)
                    tmp.replace(dest)
                    return
        raise RuntimeError(f"the sound was not ready after {READY_TIMEOUT} s: {url} (run the script again later: it "
                           "downloads this job from ve-gen-log/pending.json without a new Create Sound)")


def pending_path(layer: Path) -> Path:
    return layer / "sfx" / "ve-gen-log" / "pending.json"


def run(todo: list[dict], layer: Path, profile: Path):
    sys.path.insert(0, str(VE_RUNNER))
    import ve_runner                                   # Playwright is only needed here, not for --dry-run or tests
    from playwright.sync_api import sync_playwright

    if not ve_runner.HEADED and ve_runner.never_logged_in(profile):
        sys.exit("✗ " + ve_runner.LOGIN_HINT.format(profile=profile))
    sfx_dir = layer / "sfx"
    man_path = sfx_dir / "manifest.json"
    log_dir = sfx_dir / "ve-gen-log"                  # run.log (ve_runner.VE) and gen_sfx_ve.log, next to the sounds
    log_dir.mkdir(parents=True, exist_ok=True)

    def log(msg):
        stamp = time.strftime("%H:%M:%S")
        print(f"[{stamp}] {msg}", flush=True)
        with (log_dir / "gen_sfx_ve.log").open("a") as f:
            f.write(f"{datetime.date.today()} {stamp} {msg}\n")

    pend_path = pending_path(layer)
    made = 0
    with sync_playwright() as pw:
        ctx = ve_runner.launch_browser(pw, profile)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            ve = ve_runner.VE(page, log_dir, step=False)
            ve.open_app()                              # stops when the login has expired; never types a password
            sm = SoundMaker(ve, log)
            opened = False
            for p in todo:
                uuid = read_pending(pend_path).get(p["id"])
                if uuid:
                    log(f"{p['id']}: job {uuid} was sent in an earlier run, downloading it (no new Create Sound)")
                else:
                    if not opened:
                        sm.open()
                        opened = True
                    uuid = sm.create(p)
                    write_pending(pend_path, with_pending(read_pending(pend_path), p["id"], uuid))
                    log(f"{p['id']}: Create Sound sent (job {uuid}, written to {pend_path})")
                dest = sfx_dir / file_for(p["id"])
                sm.download(uuid, dest)
                secs = audio_seconds(dest)
                write_manifest(man_path, merge(read_manifest(man_path),
                                               make_entry(p, uuid, datetime.date.today().isoformat(), secs)))
                write_pending(pend_path, with_pending(read_pending(pend_path), p["id"], None))
                made += 1
                log(f"{p['id']}: saved {dest} ({secs if secs is not None else '?'} s), manifest updated")
        finally:
            ctx.close()
    print(f"✓ {made} sound(s) in {sfx_dir / SUBDIR}; manifest {man_path}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompts", help="the prompts file (JSON list of {id, prompt, tags, tags_zh[, duration]})")
    ap.add_argument("--dry-run", action="store_true", help="print the plan only; no browser, no credits")
    ap.add_argument("--only", nargs="+", metavar="ID", help="only these ids")
    ap.add_argument("--yes", action="store_true", help="do not ask before using VideoExpress credits")
    ap.add_argument("--profile", default=str(VE_RUNNER / ".profile"),
                    help="Chrome profile with the VideoExpress login (default: tools/ve-runner/.profile)")
    ap.add_argument("--skip-checklist", help="run even though the start checklist (tools/checklist) fails for this "
                                             "episode: give the reason, it is logged")
    a = ap.parse_args(argv)
    try:
        prompts = select(parse_prompts(json.loads(Path(a.prompts).read_text(encoding="utf-8"))), a.only)
    except (OSError, ValueError) as e:
        sys.exit(f"✗ {a.prompts}: {e}")
    loc = os.environ.get("S2F_ASSETS_LOCAL")
    layer = Path(loc).expanduser() if loc else None
    sfx_dir = layer / "sfx" if layer else None
    todo, done = split_done(prompts, read_manifest(sfx_dir / "manifest.json") if sfx_dir else [], sfx_dir)
    pending = read_pending(pending_path(layer)) if layer else {}
    print("\n".join(plan_lines(todo, done, sfx_dir, pending)))
    if a.dry_run:
        print("dry run: nothing generated")
        return
    if layer is None:
        sys.exit("✗ S2F_ASSETS_LOCAL is not set: the sounds go to your user layer, see assets/README.md")
    if not todo:
        print("✓ nothing to do")
        return
    sys.path.insert(0, str(REPO / "tools/checklist"))
    import checklist
    checklist.gate(a.prompts, "start", a.skip_checklist, "ve")
    if not confirm(sum(p["id"] not in pending for p in todo), a.yes, sys.stdin.isatty()):
        sys.exit("✗ not confirmed: run again in a terminal and answer y, or add --yes")
    run(todo, layer, Path(a.profile).expanduser())


if __name__ == "__main__":
    main()
