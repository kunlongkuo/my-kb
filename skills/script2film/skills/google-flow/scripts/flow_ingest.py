#!/usr/bin/env python3
"""Take a file downloaded from Google Flow or Flow Music into a project, with a record of where it came from.

The browser part (submit, wait, download) is done in the user's own Chrome; see skills/google-flow/SKILL.md.
This script does the fixed part after the download:

  python3 skills/google-flow/scripts/flow_ingest.py --latest video --to <project>/ve_<look>/shot3.mp4 \
      --model "Omni 1.2 Flash" --settings "360p, 10 s, 16:9, downloaded 720p" --prompt-file prompt.txt
  python3 skills/google-flow/scripts/flow_ingest.py --latest music --to <project>/flow_bgm.mp3 \
      --model "Flow Music (Lyria)" --prompt-file sound.txt --doc <project>/doc.json

--latest picks the newest finished download of that kind in ~/Downloads (or --downloads DIR) from the last
--since minutes (default 30); --from FILE takes a given file instead. The file is moved, never copied over
an existing one (--force replaces it). Next to it: <name>.flow.json (provider, model, settings, prompt, source
name, SHA-256, length) and, for a video, <name>.sheet.jpg (ten frames, one per tenth of the clip) to look at
before using it. With --doc (music only) doc.json gets bgm.src and bgm.credit, like tools/music3 collect.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".webm"}
MUSIC_EXT = {".wav", ".mp3", ".m4a", ".flac"}
PARTIAL_EXT = {".crdownload", ".download", ".part", ".tmp"}
NOTICE = ("AI-generated with Google {provider}. Google does not claim ownership of the output; outputs carry an "
          "invisible SynthID watermark. Label the published film as AI-generated (--synthetic) and check the "
          "current Google terms before commercial use.")


def kind_of(path: Path) -> str | None:
    ext = path.suffix.lower()
    return "video" if ext in VIDEO_EXT else "music" if ext in MUSIC_EXT else None


def pick_latest(files: list[Path], kind: str, since_s: float, now: float) -> Path | None:
    """Newest finished file of this kind changed within since_s seconds. None while a partial download of the
    same kind is newer than it (the browser is still writing)."""
    fresh = [f for f in files if now - f.stat().st_mtime <= since_s]
    done = [f for f in fresh if kind_of(f) == kind]
    if not done:
        return None
    best = max(done, key=lambda f: f.stat().st_mtime)
    partial = [f for f in fresh if f.suffix.lower() in PARTIAL_EXT and f.stat().st_mtime >= best.stat().st_mtime]
    return None if partial else best


def sidecar(*, kind: str, model: str, settings: str, prompt: str, source_name: str, sha256: str,
            seconds: float | None, created: str) -> dict:
    provider = "Flow" if kind == "video" else "Flow Music"
    return {"provider": f"Google {provider}", "model": model, "settings": settings, "prompt": prompt,
            "source_name": source_name, "sha256": sha256, "seconds": seconds, "ingested": created,
            "notice": NOTICE.format(provider=provider)}


def set_bgm(doc: dict, src: str, credit: str) -> dict:
    out = dict(doc)
    bgm = dict(out.get("bgm") or {})
    bgm["src"], bgm["credit"] = src, credit
    out["bgm"] = bgm
    return out


def probe_seconds(path: Path) -> float | None:
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, check=True)
        return round(float(r.stdout.strip()), 3)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def contact_sheet(video: Path, out: Path, seconds: float) -> bool:
    """Ten frames, one per tenth of the clip, in a 5x2 grid."""
    times = [seconds * (i + 0.5) / 10 for i in range(10)]
    inputs = []
    for t in times:
        inputs += ["-ss", f"{t:.2f}", "-i", str(video)]
    scale = ";".join(f"[{i}:v]scale=320:-2,setsar=1[f{i}]" for i in range(10))
    rows = "".join(f"[f{i}]" for i in range(5)) + "hstack=5[r0];" + "".join(f"[f{i}]" for i in range(5, 10)) + "hstack=5[r1]"
    graph = f"{scale};{rows};[r0][r1]vstack=2[out]"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[out]",
                        "-frames:v", "1", str(out)], capture_output=True, text=True)
    return r.returncode == 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--latest", choices=["video", "music"], help="newest finished download of this kind")
    src.add_argument("--from", dest="src", type=Path, help="this file instead")
    ap.add_argument("--to", type=Path, required=True, help="destination file in the project")
    ap.add_argument("--model", required=True, help="model as shown in Flow, e.g. 'Omni 1.2 Flash'")
    ap.add_argument("--settings", default="", help="e.g. '360p, 10 s, 9:16, downloaded 720p'")
    ap.add_argument("--prompt-file", type=Path, help="the prompt (and lyrics) exactly as submitted")
    ap.add_argument("--doc", type=Path, help="music only: set bgm.src and bgm.credit in this doc.json")
    ap.add_argument("--downloads", type=Path, default=Path.home() / "Downloads")
    ap.add_argument("--since", type=float, default=30, help="minutes back for --latest (default 30)")
    ap.add_argument("--force", action="store_true", help="replace an existing destination file")
    a = ap.parse_args(argv)

    if a.src:
        source = a.src
        if not source.is_file():
            sys.exit(f"no such file: {source}")
    else:
        files = [f for f in a.downloads.iterdir() if f.is_file()] if a.downloads.is_dir() else []
        source = pick_latest(files, a.latest, a.since * 60, time.time())
        if source is None:
            sys.exit(f"no finished {a.latest} download in {a.downloads} from the last {a.since:g} min "
                     "(still downloading, or the browser blocked it: allow automatic downloads for the site)")
    kind = kind_of(source)
    if kind is None:
        sys.exit(f"not a video or audio file: {source.name}")
    if a.latest and kind != a.latest:
        sys.exit(f"{source.name} is {kind}, not {a.latest}")
    if a.doc and kind != "music":
        sys.exit("--doc is for music only")
    dest = a.to
    if dest.suffix.lower() != source.suffix.lower():
        sys.exit(f"--to must keep the downloaded extension {source.suffix} (got {dest.suffix or 'none'})")
    if dest.exists() and not a.force:
        sys.exit(f"{dest} exists; pass --force to replace it")
    prompt = a.prompt_file.read_text(encoding="utf-8").strip() if a.prompt_file else ""

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(dest))
    sha = hashlib.sha256(dest.read_bytes()).hexdigest()
    seconds = probe_seconds(dest)
    meta = sidecar(kind=kind, model=a.model, settings=a.settings, prompt=prompt, source_name=source.name,
                   sha256=sha, seconds=seconds, created=datetime.now().isoformat(timespec="seconds"))
    side = dest.with_name(dest.name + ".flow.json")
    side.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{dest}  ({seconds} s)\n{side}")

    if kind == "video" and seconds:
        sheet = dest.with_name(dest.stem + ".sheet.jpg")
        print(sheet if contact_sheet(dest, sheet, seconds) else "contact sheet failed (ffmpeg)")
    if a.doc:
        doc = json.loads(a.doc.read_text(encoding="utf-8"))
        rel = Path(dest).resolve().relative_to(a.doc.resolve().parent) if dest.resolve().is_relative_to(
            a.doc.resolve().parent) else dest.resolve()
        credit = f"Music: Google Flow Music ({a.model}), AI-generated"
        a.doc.write_text(json.dumps(set_bgm(doc, str(rel), credit), ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
        print(f"{a.doc}: bgm.src = {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
