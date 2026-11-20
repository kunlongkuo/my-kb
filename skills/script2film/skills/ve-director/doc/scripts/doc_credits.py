"""The closing credits page (scenes/credits.js) built from what the episode already records, so nobody types it by hand:
every source that needs a credit goes on the last page.

A credits beat without "groups" gets them here (doc_code.py):
  照片   the rows of <project>/assets/CREDITS.md whose file the doc uses (any "src" / "fg" under assets/): 誰：作者（授權）,
         誰 from that photo layer's cap
  資料來源 the outlets in the 出處 column of doc.json "facts" (rows that start with 同 point at another row)
  畫面與配樂 VE shots → AI 畫面 line; a TalkingPhoto host (pip / side / host beats) → host line; bgm.credit → 配樂 line.
         Tool names (VideoExpress, TalkingPhoto) only when doc.json "name_tools" is true, i.e. a show about those tools
"""
import json, re
from pathlib import Path

PER_LINE = 4   # outlets joined with ・ on one line


def md_table(path):
    """Rows of the first markdown table in a file, as dicts keyed by its header."""
    head, rows = None, []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            if head:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if head is None:
            head = cells
        elif not set("".join(cells)) <= set("-: "):
            rows.append(dict(zip(head, cells)))
    return rows


def outlet(text):
    """The outlet named at the start of a 出處 cell: 'USA Today（Yahoo Sports 轉載，2026-08-18）https://…' → 'USA Today'."""
    s = re.split(r"（|\(|https?://|；", text, maxsplit=1)[0].strip()
    if re.match(r"[一-鿿]", s):
        return re.match(r"[一-鿿]+", s).group(0)
    words = []
    for w in s.split():
        if not (w[0].isupper() or "." in w):   # a date, a lower-case word or a CJK note ends the name
            break
        words.append(w)
    return " ".join(words)


def outlets(facts_rows):
    names = []
    for r in facts_rows:
        cell = r.get("出處", "")
        if not cell or cell.startswith("同"):
            continue
        for piece in cell.split("；"):
            n = outlet(piece)
            if n and n not in names:
                names.append(n)
    # 'Baseball-Reference' and 'Baseball-Reference Bullpen' are one outlet: keep the shorter
    return [n for n in names if not any(m != n and n.startswith(m + " ") for m in names)]


def used_assets(doc):
    return set(re.findall(r'"(?:src|fg)":\s*"assets/([^"]+)"', json.dumps(doc.get("beats", []), ensure_ascii=False)))


def subjects(doc):
    """{asset file: who or what it shows}, from the photo layers' captions ('Jackson Chourio（2025）' → 'Jackson Chourio')."""
    out = {}
    for b in doc.get("beats", []):
        for o in b.get("params", {}).get("photos", []):
            if o.get("cap") and str(o.get("src", "")).startswith("assets/"):
                out.setdefault(o["src"][len("assets/"):], re.sub(r"[（(][^）)]*[）)]\s*$", "", o["cap"]).strip())
    return out


def credit_groups(P, doc):
    groups, used = [], used_assets(doc)
    cred = P / "assets/CREDITS.md"
    if cred.is_file():
        rows = [r for r in md_table(cred) if r.get("檔案") in used]
        if rows:
            commons = all("wikimedia" in r.get("原檔", "").lower() for r in rows)
            who = subjects(doc)
            author = lambda r: re.sub(r"[（(][^）)]*[）)]", "", r["作者"]).strip()   # 'Grassferry49（en.wikipedia）' → 'Grassferry49'
            lines = [(f"{who[r['檔案']]}：" if who.get(r["檔案"]) else "") + f"{author(r)}（{r['授權']}）" for r in rows]
            if '"fg"' in json.dumps(doc.get("beats", [])):   # a 2.5D layer ("fg": "auto" or a png) is a cut-out of the photo
                lines.append("部分照片經去背，沿用原授權")
            groups.append({"head": "照片（Wikimedia Commons）" if commons else "照片", "lines": lines})
    if doc.get("facts") and (P / doc["facts"]).is_file():
        names = outlets(md_table(P / doc["facts"]))
        if names:
            groups.append({"head": "資料來源", "lines": ["・".join(names[i:i + PER_LINE]) for i in range(0, len(names), PER_LINE)]})
    beats = doc.get("beats", [])
    made, tool = [], (lambda name: f"（{name}）" if doc.get("name_tools") else "")
    if any(b.get("source") == "ve" for b in beats):
        made.append("部分畫面為 AI 生成" + tool("VideoExpress"))
    if doc.get("pip") or doc.get("side") or any(b.get("source") == "host" for b in beats):
        made.append("主持人畫面為 AI 生成" + tool("TalkingPhoto"))
    if doc.get("bgm", {}).get("credit"):
        made.append("配樂：" + doc["bgm"]["credit"])
    if made:
        groups.append({"head": "畫面與配樂", "lines": made})
    return groups
