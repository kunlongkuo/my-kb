#!/usr/bin/env python3
"""Mechanical checks for a ve-director plan.md (run before CP1).

Usage: plan_lint.py PLAN --min 30 --max 45 --names 王生   (proper names only: the 角色 block's 名字 column, never role nouns like 美女)
Exit code 0 = all checks pass, 1 = at least one FAIL.

The plan must contain a fenced ledger block:

```ledger
S1 開始 | Actor 1 | 院牆外 | 站 | 院門前
S1 結束 | Actor 1 | 院牆外 | 站 | 院門前
S2 開始 | Actor 1 | 院牆外 | 站 | 牆塌陷處前 | 省略：沿牆走到塌陷處
S4 開始 | 彩筆 | 屋內 | 握著 | Actor 2 右手
```
Fields: shot+phase | entity (Actor N or a prop) | 區域 (which side of which boundary) | 姿勢或狀態 | 所在 (next to what / in whose hand) | optional 省略：<reason>
"""
import argparse
import re
import sys


def table_rows(text):
    lines = [l for l in text.splitlines() if l.startswith("|")]
    if not lines:
        return [], []
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = []
    for l in lines[2:]:
        cells = [c.strip() for c in l.strip("|").split("|")]
        if cells and re.fullmatch(r"\d+", cells[0]):
            rows.append(dict(zip(header, cells)))
    return header, rows


def col(header, prefix):
    for h in header:
        if h.startswith(prefix):
            return h
    return None


def main():
    ap = argparse.ArgumentParser(description="Mechanical checks for a ve-director plan.md (run before CP1). "
                                             "Exit 0 when every check passes, 1 on any FAIL.")
    ap.add_argument("plan", help="the plan.md")
    ap.add_argument("--min", type=int, required=True, help="lower bound of the total length, seconds")
    ap.add_argument("--max", type=int, required=True, help="upper bound of the total length, seconds")
    ap.add_argument("--names", default="", help="proper names only (the cast block's name column), comma-separated")
    a = ap.parse_args()
    text = open(a.plan, encoding="utf-8").read()
    names = [n for n in a.names.split(",") if n]
    fails = []

    def fail(code, msg):
        fails.append(f"FAIL {code}: {msg}")

    # --- table ---
    table_part = text.split("## 鏡頭規劃表", 1)[1] if "## 鏡頭規劃表" in text else text
    header, rows = table_rows(table_part)
    if not rows:
        print("FAIL P0: no shot table rows found")
        return 1
    people_col = col(header, "畫面中的人")
    sec_col = col(header, "秒數")
    for need in ["開始狀態", "結束狀態"]:
        if not col(header, need):
            fail("P0", f"table has no '{need}' column")
    total = 0
    shot_actors = {}
    for r in rows:
        n = r[header[0]]
        try:
            s = int(re.sub(r"\D", "", r.get(sec_col, "")) or "0")
        except ValueError:
            s = 0
        if not 3 <= s <= 10:
            fail("P3", f"shot {n}: {s}s outside 3-10s")
        total += s
        people = r.get(people_col, "")
        actors = re.findall(r"(Actor \d+)（(臉可見|臉不可見)）", people)
        bare = set(re.findall(r"Actor \d+", people)) - {x for x, _ in actors}
        for b in sorted(bare):
            fail("P5", f"shot {n}: {b} lacks （臉可見）/（臉不可見）")
        ids = sorted({x for x, _ in actors} | bare)
        if len(ids) > 2:
            fail("P6", f"shot {n}: {len(ids)} Actors in frame (cap 2)")
        shot_actors[n] = ids
        if names:
            skip = {"原文動作"}
            for h, v in r.items():
                if any(h.startswith(k) for k in skip):
                    continue
                v2 = re.sub(r'「[^」]*」|"[^"]*"', "", v)
                for nm in names:
                    if nm in v2:
                        fail("P4", f"shot {n}: name '{nm}' in column '{h}'")
    if not a.min <= total <= a.max:
        fail("P3", f"total {total}s outside {a.min}-{a.max}s")

    # --- ledger ---
    m = re.search(r"```ledger\n(.*?)```", text, re.S)
    if not m:
        fail("P1", "no ```ledger block")
        ledger = []
    else:
        ledger = []
        for i, line in enumerate(m.group(1).splitlines(), 1):
            if not line.strip():
                continue
            f = [x.strip() for x in line.split("|")]
            mm = re.fullmatch(r"S(\d+)\s*(開始|結束)", f[0])
            if not mm or len(f) < 5:
                fail("P1", f"ledger line {i} malformed: {line.strip()}")
                continue
            note = f[5] if len(f) > 5 else ""
            ledger.append((int(mm.group(1)), mm.group(2), f[1], f[2], f[3], f[4], note))
    have = {(s, ph, e) for s, ph, e, *_ in ledger}
    for n, ids in shot_actors.items():
        for actor in ids:
            for ph in ("開始", "結束"):
                if (int(n), ph, actor) not in have:
                    fail("P1", f"shot {n}: ledger lacks '{ph}' for {actor}")
    # cross-cut continuity: an entity's next 開始 must equal its last 結束 unless an 省略 reason is given
    last = {}
    for s, ph, e, zone, pose, where, note in sorted(ledger, key=lambda x: (x[0], 0 if x[1] == "開始" else 1)):
        if ph == "開始" and e in last:
            ps, pz, pp, pw = last[e]
            diffs = [k for k, x, y in (("區域", pz, zone), ("姿勢", pp, pose), ("所在", pw, where)) if x != y]
            if diffs and not note.startswith("省略："):
                fail("P2", f"{e}: S{ps} 結束 → S{s} 開始 changes {'/'.join(diffs)} "
                           f"({pz}/{pp}/{pw} → {zone}/{pose}/{where}) with no 省略：reason")
            elif diffs and len(note) <= len("省略："):
                fail("P2", f"{e}: S{s} 開始 has an empty 省略：reason")
        if ph == "結束":
            last[e] = (s, zone, pose, where)

    # --- trailer lines ---
    for need in ["原文動作對照：", "連戲檢查："]:
        if need not in text:
            fail("P7", f"missing line '{need}'")

    for f in fails:
        print(f)
    print(f"{len(rows)} shots, {total}s, {len(ledger)} ledger lines, {len(fails)} fail(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
