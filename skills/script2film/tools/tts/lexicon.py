"""讀音表（tools/tts/lexicon.json）：送去語音合成之前換掉會唸錯的字。所有系列共用這一份。

  spoken(text, lang)      套用 lang 相同的規則後的字串；同一條規則套幾次結果都一樣（to 裡包含 from 的也是）。
                          規則之間不要互相接力（一條的 to 是另一條的 from），那樣套兩次會不同；測試會擋
  changes(text, lang)     實際換了的 [(from, to), ...]
  python3 tools/tts/lexicon.py <doc.json>     列出這一集「讀音表換的」與「這一集自己改的」

機器抓不到沒進表的多音字：聽出來一個，就在 lexicon.json 加一條（整個詞的規則放在單字規則上面）。
"""
import json
import sys
from pathlib import Path

TABLE = Path(__file__).resolve().parent / "lexicon.json"
HOLD = ""   # 私用區字元，旁白裡不會出現：先把已經是 to 的地方收起來，to 裡面包含 from 的規則才不會越套越多


def load(path=TABLE):
    return json.loads(Path(path).read_text(encoding="utf-8"))["rules"]


def problems(rules):
    """表本身的問題：from 是空的、兩條 from 相同。"""
    bad = [f"rule {i}: from is empty" for i, r in enumerate(rules, 1) if not r.get("from")]
    seen = {}
    for i, r in enumerate(rules, 1):
        k = (r.get("from"), r.get("lang"))
        if k in seen and r.get("from"):
            bad.append(f"rules {seen[k]} and {i} both have from {r['from']}")
        seen.setdefault(k, i)
    return bad


def _apply(text, rules, lang):
    done = []
    for r in rules:
        if r.get("lang", lang) != lang or not r.get("from"):
            continue
        new = text.replace(r["to"], HOLD).replace(r["from"], r["to"]).replace(HOLD, r["to"])
        if new != text:
            done.append((r["from"], r["to"]))
        text = new
    return text, done


def spoken(text, lang, rules=None):
    return _apply(text, load() if rules is None else rules, lang)[0]


def changes(text, lang, rules=None):
    return _apply(text, load() if rules is None else rules, lang)[1]


def _bare(s):
    return "".join(s.split()).rstrip("。？！.?!")


USAGE = """Pronunciation table (tools/tts/lexicon.json): words swapped before speech synthesis, shared by every series.

  spoken(text, lang)      the text after the rules for lang; applying a rule again gives the same result (also when its
                          to contains its from). Rules must not chain (one rule's to being another's from), since applying
                          twice would then differ; a test guards this
  changes(text, lang)     the [(from, to), ...] actually swapped
  python3 tools/tts/lexicon.py <doc.json>     list what the table swapped and what this episode changed itself

A mispronounced word that is not in the table goes unnoticed by the machine: when you hear one, add a rule to
lexicon.json (rules for whole words above rules for single characters)."""


def main():
    if len(sys.argv) != 2:
        sys.exit(USAGE)
    doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    lang, rules = doc["lang"], load()
    table, own = [], []
    for n, line in enumerate(doc["lines"], 1):
        src = line.get("tts") or line["text"]
        if (c := changes(src, lang, rules)):
            table.append(f"  line {n}: " + ", ".join(f"{a}→{b}" for a, b in c))
        if line.get("tts") and _bare(line["tts"]) != _bare(line["text"]):
            own.append(f"  line {n}: {line['text']}\n      spoken: {line['tts']}")
    print(f"Swapped by the pronunciation table ({len(table)} lines):")
    print("\n".join(table) or "  none")
    print(f"Changed in this episode ({len(own)} lines; words that apply everywhere go in tools/tts/lexicon.json):")
    print("\n".join(own) or "  none")


if __name__ == "__main__":
    main()
