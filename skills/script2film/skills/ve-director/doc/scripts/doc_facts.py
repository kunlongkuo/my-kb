"""The episode's fact list: facts.md next to doc.json, checked against what the code shots put on screen.

facts.md holds one Markdown table with the columns 畫面｜等級｜出處｜原文摘錄｜備註 (FORMAT §9), or their English names
on screen | tier | source | excerpt | note (any case); a tier is 原始｜權威二手｜線索 or primary | secondary | lead. doc_lint's `facts` rule calls
check(doc, base). What has to be in the list (design D2):
  - every scripture reference written anywhere in a code beat's params (「出埃及記 14:13」, 「（出 15:24）」): a row whose 出處
    covers it. Only 書卷＋章:節 counts; a chapter or chapter range (「出埃及記 13–21 章」) is not a reference.
  - quote_card text: a row whose 畫面 is the same text; when `by` is a reference, every part of the text (split at ……)
    must be in that row's 原文摘錄, punctuation aside.
  - stat_count value: a row whose 備註 names the beat and whose 畫面 has that number.
  - pie, line_chart, breakdown: a row whose 備註 names the beat (one source row
    per chart, not one per number; formula is a relation of words and is not checked).
  - a row used by any of these must not be 線索.
A beat with params "fact": false is skipped (the speaker's own words, the next-episode card).
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[4] / "tools/config"))
import s2f_config; s2f_config.load()
import re
from pathlib import Path

COLUMNS = ("畫面", "等級", "出處", "原文摘錄", "備註")
TIERS = ("原始", "權威二手", "線索")
# English names, read case-insensitively; rows keep the Chinese keys and tier values (doc/README.md "facts.md")
COLUMN_EN = {"on screen": "畫面", "tier": "等級", "source": "出處", "excerpt": "原文摘錄", "note": "備註"}
TIER_EN = {"primary": "原始", "secondary": "權威二手", "lead": "線索"}
EN_OF = {zh: en for en, zh in {**COLUMN_EN, **TIER_EN}.items()}
CHARTS = ("pie", "line_chart", "breakdown")   # chart beats that need a source row (D11)

# 和合本 book names and their usual abbreviations
BOOKS = [("創世記", "創"), ("出埃及記", "出"), ("利未記", "利"), ("民數記", "民"), ("申命記", "申"), ("約書亞記", "書"),
         ("士師記", "士"), ("路得記", "得"), ("撒母耳記上", "撒上"), ("撒母耳記下", "撒下"), ("列王紀上", "王上"),
         ("列王紀下", "王下"), ("歷代志上", "代上"), ("歷代志下", "代下"), ("以斯拉記", "拉"), ("尼希米記", "尼"),
         ("以斯帖記", "斯"), ("約伯記", "伯"), ("詩篇", "詩"), ("箴言", "箴"), ("傳道書", "傳"), ("雅歌", "歌"),
         ("以賽亞書", "賽"), ("耶利米書", "耶"), ("耶利米哀歌", "哀"), ("以西結書", "結"), ("但以理書", "但"),
         ("何西阿書", "何"), ("約珥書", "珥"), ("阿摩司書", "摩"), ("俄巴底亞書", "俄"), ("約拿書", "拿"), ("彌迦書", "彌"),
         ("那鴻書", "鴻"), ("哈巴谷書", "哈"), ("西番雅書", "番"), ("哈該書", "該"), ("撒迦利亞書", "亞"), ("瑪拉基書", "瑪"),
         ("馬太福音", "太"), ("馬可福音", "可"), ("路加福音", "路"), ("約翰福音", "約"), ("使徒行傳", "徒"), ("羅馬書", "羅"),
         ("哥林多前書", "林前"), ("哥林多後書", "林後"), ("加拉太書", "加"), ("以弗所書", "弗"), ("腓立比書", "腓"),
         ("歌羅西書", "西"), ("帖撒羅尼迦前書", "帖前"), ("帖撒羅尼迦後書", "帖後"), ("提摩太前書", "提前"),
         ("提摩太後書", "提後"), ("提多書", "多"), ("腓利門書", "門"), ("希伯來書", "來"), ("雅各書", "雅"), ("彼得前書", "彼前"),
         ("彼得後書", "彼後"), ("約翰一書", "約一"), ("約翰二書", "約二"), ("約翰三書", "約三"), ("猶大書", "猶"), ("啟示錄", "啟")]
BOOK_OF = {n: full for full, ab in BOOKS for n in (full, ab)}
_NAMES = "|".join(sorted(BOOK_OF, key=len, reverse=True))   # longest first: 約翰福音 before 約, 撒上 before 撒
REF = re.compile(rf"({_NAMES})\s*(\d+)\s*[:：]\s*(\d+)(?:\s*[-–—~]\s*(\d+)(?:\s*[:：]\s*(\d+))?)?")


def refs(text):
    """Scripture references in text → [(written text, book, (chapter, verse) start, (chapter, verse) end)]."""
    out = []
    for m in REF.finditer(text):
        book, c, v, a, b = BOOK_OF[m[1]], int(m[2]), int(m[3]), m[4], m[5]
        end = (int(a), int(b)) if b else (c, int(a)) if a else (c, v)
        out.append((m[0], book, (c, v), end))
    return out


def covers(row, ref):
    return any(r[1] == ref[1] and r[2] <= ref[2] and ref[3] <= r[3] for r in refs(row["出處"]))


def bare(s):
    """Text without punctuation or spaces, for comparing a quote with its source."""
    return re.sub(r"[\W_]+", "", s)


def both(zh):
    """A column or tier for messages: the Chinese name and the English one, 備註/note."""
    return f"{zh}/{EN_OF[zh]}"


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def column(name):
    """A header cell → its Chinese column name (an English name, any case, maps to it); anything else as written."""
    return COLUMN_EN.get(name.lower(), name)


def read(path):
    """facts.md → (rows with their file line number in "line", problems); rows is None when the table cannot be read.
    Rows are keyed by the Chinese column names and their 等級 is the Chinese tier, whichever language the file uses; the
    tier as written is kept in "tier_as_written" for messages."""
    if not path.exists():
        return None, [f"facts: {path}: no such file"]
    lines = path.read_text(encoding="utf-8").splitlines()
    head = next((i for i, x in enumerate(lines) if x.strip().startswith("|") and "畫面" in map(column, cells(x))), None)
    if head is None:
        return None, [f"facts: {path.name} has no table with a {both('畫面')} column"]
    cols = [column(c) for c in cells(lines[head])]
    missing = [both(c) for c in COLUMNS if c not in cols]
    if missing:
        return None, [f"facts: {path.name} line {head + 1}: the table lacks the column{'s' if len(missing) > 1 else ''} {', '.join(missing)}"]
    rows, bad = [], []
    for i in range(head + 2, len(lines)):
        if not lines[i].strip().startswith("|"):
            break
        row = {**dict(zip(cols, cells(lines[i]) + [""] * len(cols))), "line": i + 1}
        row["tier_as_written"] = row["等級"]
        row["等級"] = TIER_EN.get(row["等級"].lower(), row["等級"])
        if row["等級"] not in TIERS:
            bad.append(f"facts: {path.name} line {i + 1}: tier \"{row['tier_as_written']}\" is not one of "
                       f"{' / '.join(TIERS)} ({' / '.join(TIER_EN)})")
        rows.append(row)
    return rows, bad


def strings(v):
    """Every string inside a params value (nested dicts and lists included)."""
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from strings(x)


def scripture_note(doc):
    """One line for a doc with a facts list: quotes are compared with the excerpts in facts.md only. Nothing here reads a
    full Bible text, so the excerpts themselves are trusted."""
    if doc.get("facts"):
        return ("facts: Bible quotes are compared only with the excerpts in facts.md, not with a full Bible text "
                "(copy the excerpts from the Bible and have someone check them)")
    return None


def check(doc, base):
    """Problems with doc.json "facts" (a path relative to base, the episode folder); [] when the doc has no "facts"."""
    if not doc.get("facts"):
        return []
    rows, out = read(Path(base) / doc["facts"])
    if rows is None:
        return out
    used = []
    for b in doc["beats"]:
        p = b.get("params") or {}
        if b.get("source") != "code" or p.get("fact") is False:
            continue
        bid = b["id"]
        for s in strings(p):
            for ref in refs(s):
                hit = [r for r in rows if covers(r, ref)]
                used += hit
                if not hit:
                    out.append(f"facts: {bid} the reference \"{ref[0]}\" on screen has no row in facts.md")
        if b.get("scene") == "quote_card" and p.get("text"):
            hit = [r for r in rows if bare(r["畫面"]) == bare(p["text"])]
            used += hit
            by = refs(p.get("by", ""))
            if not hit:
                out.append(f"facts: {bid} quote card \"{p['text']}\" has no row in facts.md "
                           f"(the {both('畫面')} column must be the same text)")
            elif by:
                parts = [bare(x) for x in re.split(r"…+|\.{3,}", p["text"]) if bare(x)]
                src = [r for r in hit if covers(r, by[0])]
                if not src:
                    out.append(f"facts: {bid} quote card's row (line {hit[0]['line']}) has a {both('出處')} other than {by[0][0]}")
                elif not all(x in bare(src[0]["原文摘錄"]) for x in parts):
                    out.append(f"facts: {bid} quote card text does not match the {both('原文摘錄')} on line {src[0]['line']}")
        if b.get("scene") == "stat_count" and "value" in p:
            v = p["value"]
            n = str(int(v)) if float(v).is_integer() else str(v)
            hit = [r for r in rows if re.search(rf"(?<![A-Za-z0-9]){re.escape(bid)}(?![A-Za-z0-9])", r["備註"])
                   and re.search(rf"(?<![\d.]){re.escape(n)}(?![\d.])", r["畫面"])]
            used += hit
            if not hit:
                out.append(f"facts: {bid} number {n} has no row in facts.md ({both('備註')} naming {bid}, {both('畫面')} with {n})")
        if b.get("scene") in CHARTS:
            hit = [r for r in rows if re.search(rf"(?<![A-Za-z0-9]){re.escape(bid)}(?![A-Za-z0-9])", r["備註"])]
            used += hit
            if not hit:
                out.append(f"facts: {bid} chart data has no row in facts.md ({both('備註')} naming {bid})")
    for r in {r["line"]: r for r in used}.values():
        if r["等級"] == "線索":
            out.append(f"facts: line {r['line']} is only a lead (tier \"{r['tier_as_written']}\"): a lead does not go on screen")
    return out
