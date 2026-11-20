"""Answer and wait on ve_runner QC gates without a TTY (the runner reads runs/<ts>/decision.txt).

  python3 ve_qc.py runs/<ts>            # wait until the runner is waiting at a QC gate (returns at once if it already is)
  python3 ve_qc.py runs/<ts> 2          # answer the waiting gate (1/2/r/s/q; s = skip the shot, no video), then wait for the next gate or the end

Prints the gate label and the side-by-side compare image. Exit 0 = at a gate, 2 = run finished, 1 = run failed or timeout.
Watch run.log, not the runner's stdout: redirected stdout is block-buffered.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

DONE = re.compile(r"all \d+ shot\(s\) submitted")
FAILED = re.compile(r"Traceback|^\S+ (stopped|crashed):", re.M)


def state(log: str) -> dict:
    """Parse run.log: how many gates opened and answered, the last gate's label/compare, finished or failed."""
    waits = log.count("QC WAITING")
    answers = len(re.findall(r"^\S+ decision: ", log, re.M))
    gates = re.findall(r"^\S+ QC (\S+): (\d+) candidate\(s\)(?:; compare (.+))?$", log, re.M)
    label, n, compare = gates[-1] if gates else (None, None, None)
    return {"waits": waits, "pending": waits > answers, "label": label, "n": int(n) if n else None,
            "compare": compare or None, "done": bool(DONE.search(log)), "failed": bool(FAILED.search(log))}


def report(s: dict) -> int:
    if s["failed"]:
        print("run failed (see run.log)")
        return 1
    if s["pending"]:
        print(f"QC {s['label']}: {s['n']} candidate(s)" + (f"\ncompare: {s['compare']}" if s["compare"] else ""))
        return 0
    print("run finished: all shots submitted")
    return 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("choice", nargs="?", help="1/2/…, r (re-roll), s (skip this shot) or q (quit) for the waiting gate")
    ap.add_argument("--timeout", type=float, default=1800, help="seconds to wait (default 1800)")
    a = ap.parse_args(argv)
    run = Path(a.run_dir)
    log = run / "run.log"
    read = lambda: log.read_text(encoding="utf-8") if log.exists() else ""  # noqa: E731
    s = state(read())
    if a.choice:
        if not s["pending"]:
            print("no QC gate is waiting; nothing answered")
            return 1
        (run / "decision.txt").write_text(a.choice)
        target = s["waits"]  # answered: wait for a new gate beyond this one
    else:
        if s["pending"] or s["done"] or s["failed"]:
            return report(s)
        target = s["waits"]
    deadline = time.time() + a.timeout
    while time.time() < deadline:
        s = state(read())
        if s["failed"] or (s["done"] and not s["pending"]) or (s["waits"] > target and s["pending"]):
            return report(s)
        time.sleep(2)
    print(f"timeout after {a.timeout:.0f}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
