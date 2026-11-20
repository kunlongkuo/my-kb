"""開工清單：三層（通則／格式／系列）、兩段（開工前 start／出片前 release）。

  python3 tools/checklist/checklist.py run <集資料夾> --stage start      開工前
  python3 tools/checklist/checklist.py run <集資料夾> --stage release    出片前（先跑開工前的全部項目）
  python3 tools/checklist/checklist.py questions <集資料夾> --stage start|release    這一段要回答的題目與目前的答案
  python3 tools/checklist/checklist.py answer <集資料夾> <題目代號> "<這一集的答案>"

集資料夾裡有 doc.json 是解說長片格式，有 day.json 是書頁短片格式（書頁短片只跑通則層）。
上一層有 series.json 才跑系列層；沒有就當單集。系列可以在 series.json 宣告某一項不適用，要寫原因，而且只有
項目本身允許的才收：  "checklist": {"na": {"upload-fields": "<原因>"}}
每項印 ✓／✗／－（不適用）。結果寫到 <集>/nightly/checklist_<stage>.json。退出碼 0＝全過、1＝有項目不過、2＝用法或設定寫錯。

送 VE、送 TP、上傳三支程式開頭會呼叫 gate()：不過就停（出片段的 YouTube 權杖那一項會連線查權杖範圍）。硬要跳過用那三支程式的 --skip-checklist "<原因>"，
每次跳過在 <集>/nightly/checklist_skips.jsonl 留一行。
"""
import argparse, datetime, json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import items  # noqa: E402
sys.path.insert(0, str(items.DOC_SCRIPTS))
from doc_common import lines_hash  # noqa: E402  旁白指紋：答案是對著哪一版旁白寫的（doc_approval 共用同一個定義）

STAGES = ("start", "release")
FORMAT_FILES = (("doc.json", "doc"), ("day.json", "book"))


class ConfigError(Exception):
    """series.json 的 checklist 設定寫錯（不能宣告的項目、原因是空的）。"""


def read_doc(f):
    """doc.json／day.json 的內容；讀不進來或不是 JSON 物件 → ConfigError。"""
    try:
        doc = json.loads(Path(f).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ConfigError(f"cannot read {f}: {e}")
    if not isinstance(doc, dict):
        raise ConfigError(f"{f} must hold an object")
    return doc


def find_episode(path, ignored=None):
    """(集資料夾, "doc"|"book")：從 path（檔或資料夾）往上找第一個有 doc.json 或 day.json 的資料夾；它的上一層如果
    也有，就再往上一層，直到上一層沒有為止。找不到回 None。
    往上多走是因為集資料夾底下的子資料夾也會有自己的 doc.json（送 VE 用的 extra_live/、extra_collage/ 各有一份
    只列鏡頭的小稿），run sheet 就放在那裡；要檢查的是整集，不是那份小稿。只看緊鄰的上一層，所以更上面某個不相干的
    資料夾剛好有 doc.json 不會把整個系列吃掉。
    往上找到的 doc.json／day.json 讀不進來或不是 JSON 物件（別的工具的輸出、寫壞的檔），那個資料夾就不算集，接著往上找；
    略過的檔加進 ignored（給的話）。明確指定的集照樣報錯（ConfigError）：path 本身就是 doc.json／day.json，或 path 是
    資料夾而它自己就放著這兩個檔之一（tp_host.py、checklist.py run 傳的是集資料夾）。"""
    def kind(d):
        for name, fmt in FORMAT_FILES:
            f = d / name
            if f.exists():
                try:
                    read_doc(f)
                    return fmt
                except ConfigError:
                    if ignored is not None and f not in ignored:
                        ignored.append(f)
        return None
    p = Path(path).resolve()
    named = [p] if p.is_file() and p.name in dict(FORMAT_FILES) else [p / n for n, _ in FORMAT_FILES] if p.is_dir() else []
    for f in named:
        if f.exists():
            read_doc(f)
    d = next((x for x in ([p] if p.is_dir() else []) + list(p.parents) if kind(x)), None)
    if d is None:
        return None
    while kind(d.parent):
        d = d.parent
    return d, kind(d)


RULES = Path(__file__).resolve().parent / "rules.json"
PACKS = Path(__file__).resolve().parent / "packs"
ANSWERS = "checklist_answers.json"
NOT_ANSWERED, NARRATION_CHANGED = "not answered", "narration changed, confirm again"   # answer states besides "ok"


def questions(series, fmt, want, ep=None):
    """這個格式、這幾段要回答的題目：通則的（rules.json）、系列選的題目包（packs/<名>.json，series.json 的 checklist.packs）、
    系列自己寫的（checklist.rules）。題目有 when_file（集資料夾裡的相對路徑）時，只有那個檔存在才問（例如用了 MiniMax H3
    的集才有 h3/manifest.json）；沒給 ep 就不問這類題目。"""
    base = json.loads(RULES.read_text(encoding="utf-8"))["rules"]
    cfg = (series or {}).get("checklist") or {}
    own, names = cfg.get("rules") or [], cfg.get("packs") or []
    if not isinstance(own, list) or not isinstance(names, list):
        raise ConfigError("checklist.rules and checklist.packs in series.json must be arrays")
    packed = []
    for n in names:   # 題目包：工具附的幾組題目，系列自己選要用哪幾包
        p = PACKS / f"{n}.json"
        if not isinstance(n, str) or not n.replace("-", "").isalnum() or not p.exists():
            have = ", ".join(sorted(x.stem for x in PACKS.glob("*.json")))
            raise ConfigError(f"no such question pack: {n!r} (available: {have})")
        packed += json.loads(p.read_text(encoding="utf-8"))["rules"]
    out, seen = [], set()
    for r in base + packed + own:
        if not isinstance(r, dict) or not all(r.get(k) for k in ("id", "stage", "ask")):
            raise ConfigError(f"a question needs id, stage and ask: {r!r}")
        if r["id"] in seen:
            raise ConfigError(f"duplicate question id: {r['id']}")
        seen.add(r["id"])
        stages = [r["stage"]] if isinstance(r["stage"], str) else r["stage"]
        when = r.get("when_file")
        if when is not None and (ep is None or not (Path(ep) / when).exists()):
            continue
        if r.get("format") in (None, fmt) and set(stages) & set(want):
            out.append(r)
    return out


def answer_state(ep, doc, fmt, qs):
    """[(題目, "ok"|"沒答"|"旁白改過，要重新確認", 目前的答案)]"""
    p = ep / ANSWERS
    got = read_answers(p)
    h = lines_hash(doc, fmt)
    out = []
    for q in qs:
        a = got.get(q["id"]) if isinstance(got.get(q["id"]), dict) else {}
        state = NOT_ANSWERED if not str(a.get("answer", "")).strip() else "ok" if a.get("lines_hash") == h else NARRATION_CHANGED
        out.append((q, state, a.get("answer", "")))
    return out


def read_answers(p):
    """<集>/checklist_answers.json 的內容；沒有檔回空的，檔壞了就停（ConfigError）。"""
    if not p.exists():
        return {}
    try:
        got = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ConfigError(f"cannot read {p}: {e}")
    if not isinstance(got, dict):
        raise ConfigError(f"{p} must hold an object")
    return got


def load_episode(ep_dir):
    """明確指定的集資料夾：它的 doc.json／day.json 壞了 find_episode 會報出來，不會變成「沒有 doc.json」。"""
    here = Path(ep_dir).resolve()
    found = find_episode(ep_dir)
    if found is None:
        raise ConfigError(f"{ep_dir} has neither doc.json nor day.json")
    if found[0] != here:
        raise ConfigError(f"{ep_dir} is a subfolder of {found[0]}: run on the whole episode folder")
    ep, fmt = found
    return ep, fmt, read_doc(ep / dict((f, n) for n, f in FORMAT_FILES)[fmt])


def series_of(ep):
    try:
        return items.series_cfg(ep)
    except ValueError as e:
        raise ConfigError(f"cannot read the series settings: {e}")


def na_reasons(series):
    """series.json 的 checklist.na：{項目代號: 原因}。代號要是允許宣告的項目、原因不能是空的，否則 ConfigError。"""
    na = ((series or {}).get("checklist") or {}).get("na") or {}
    if not isinstance(na, dict):
        raise ConfigError("checklist.na in series.json must be {item id: reason}")
    allowed = {x["id"] for x in items.ITEMS if x["na_ok"]}
    for k, why in na.items():
        if k not in allowed:
            raise ConfigError(f"{k} cannot be declared not applicable (items that can: {', '.join(sorted(allowed)) or 'none'})")
        if not str(why).strip():
            raise ConfigError(f"the reason for {k} is empty")
    return na


def run(ep_dir, stage, environ=None, write=True, video=None):
    """跑這一集、這一段的項目（release 含 start）。回傳 {"ok", "stage", "format", "items": [{"id", "item", "state", "ok", "detail"}]}。"""
    if stage not in STAGES:
        raise ConfigError(f"stage must be {' or '.join(STAGES)}: {stage!r}")
    ep, fmt, doc = load_episode(ep_dir)
    series, series_dir = series_of(ep)
    na = na_reasons(series)
    ctx = {"ep": ep, "format": fmt, "doc": doc, "series": series, "series_dir": series_dir, "write": write,
           "environ": os.environ if environ is None else environ, "video": video}
    want = STAGES[:STAGES.index(stage) + 1]
    res = []
    if series is None:
        res.append({"id": "series", "item": "series settings", "state": "na", "ok": True, "detail": "no series.json: treated as a single episode"})
    for x in items.ITEMS:
        if x["stage"] not in want or (x["format"] and x["format"] != fmt):
            continue
        if x["layer"] == "series" and series is None:
            continue
        if x["id"] in na:
            res.append({"id": x["id"], "item": x["label"], "state": "na", "ok": True, "detail": f"not applicable ({na[x['id']]})"})
            continue
        try:
            rows = x["fn"](ctx)
        except Exception as e:   # 稿子缺欄位之類：算這一項不過，其他項照跑
            rows = [(x["label"], False, f"could not check: {type(e).__name__} {e}")]
        for name, ok, detail in rows:
            res.append({"id": x["id"], "item": name, "state": "pass" if ok else "fail", "ok": bool(ok), "detail": detail})
    todo = [(q, st) for q, st, _ in answer_state(ep, doc, fmt, questions(series, fmt, want, ep)) if st != "ok"]
    res.append({"id": "answers", "item": "answers", "state": "fail" if todo else "pass", "ok": not todo,
                "detail": "; ".join(f"{q['id']}: {st}" for q, st in todo) + (" (see the questions: checklist.py questions)" if todo else "")})
    out = {"ok": all(r["ok"] for r in res), "stage": stage, "format": fmt, "items": res}
    if write:
        (ep / "nightly").mkdir(exist_ok=True)
        (ep / f"nightly/checklist_{stage}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


MARK = {"pass": "✓", "fail": "✗", "na": "－"}


def show(out):
    for r in out["items"]:
        print(MARK[r["state"]], r["item"], r["detail"])


def log_skip(folder, step, reason, failed):
    with open(Path(folder) / "checklist_skips.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "step": step,
                            "reason": reason, "failed": failed}, ensure_ascii=False) + "\n")
    print(f"checklist skipped: {reason}")


def gate(path, stage, skip_reason, step, environ=None, outside_ok=True):
    """送 VE、送 TP、上傳開頭呼叫：path 所在的集過不了這一段就停（exit 1）。skip_reason 不是 None 時：原因空白 exit 2；
    否則記一行後放行。path 不在任何集資料夾裡：outside_ok 是 True 就照常放行（VE 也用來做沒有 doc.json 的故事片）；
    False（上傳）就停，要帶 skip_reason 才放行，紀錄寫在 path 所在的資料夾。"""
    ignored = []
    try:
        found = find_episode(path, ignored) if path else None
    except ConfigError as e:   # 明確指定的 doc.json／day.json 壞了：和設定寫錯一樣，不能用 --skip-checklist 帶過
        print(f"✗ checklist settings: {e}")
        sys.exit(2)
    for f in ignored:
        print(f"note: {f} does not hold a readable JSON object, so its folder is not an episode folder")
    if found is None:
        if outside_ok:
            print("not in an episode folder: the checklist does not apply")
            return
        print("✗ not in an episode folder, so the checklist cannot check this film: put it back in its episode folder, or pass --skip-checklist \"<reason>\"")
        if skip_reason is None:
            sys.exit(1)
        if not skip_reason.strip():
            print("✗ --skip-checklist needs a reason")
            sys.exit(2)
        p = Path(path).resolve()
        log_skip(p if p.is_dir() else p.parent, step, skip_reason.strip(), ["outside-episode"])
        return
    ep = found[0]
    print(f"checklist for: {ep}")
    try:
        p = Path(path).resolve()
        out = run(ep, stage, environ, video=p if p.is_file() and p.suffix.lower() == ".mp4" else None)
    except ConfigError as e:   # 設定寫錯不能用 --skip-checklist 帶過：先把 series.json 改對
        print(f"✗ checklist settings: {e}")
        sys.exit(2)
    if out["ok"]:
        return
    bad = [r for r in out["items"] if not r["ok"]]
    for r in bad:
        print("✗", r["item"], r["detail"])
    if skip_reason is None:
        sys.exit(1)
    if not skip_reason.strip():
        print("✗ --skip-checklist needs a reason")
        sys.exit(2)
    (ep / "nightly").mkdir(exist_ok=True)
    log_skip(ep / "nightly", step, skip_reason.strip(), sorted({r["id"] for r in bad}))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Start checklist: three layers (base, format, series), two stages (start, release).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("episode")
    r.add_argument("--stage", required=True, choices=STAGES)
    q = sub.add_parser("questions")
    q.add_argument("episode")
    q.add_argument("--stage", required=True, choices=STAGES)
    w = sub.add_parser("answer")
    w.add_argument("episode")
    w.add_argument("id")
    w.add_argument("text")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "questions":
            ep, fmt, doc = load_episode(a.episode)
            for qn, st, ans in answer_state(ep, doc, fmt, questions(series_of(ep)[0], fmt, STAGES[:STAGES.index(a.stage) + 1], ep)):
                print(f"{MARK['pass' if st == 'ok' else 'fail']} {qn['id']} ({st})\n   Q: {qn['ask']}\n   source: {qn.get('source') or '—'}\n   A: {ans or '—'}")
            return 0
        if a.cmd == "answer":
            ep, fmt, doc = load_episode(a.episode)
            known = {r["id"] for r in questions(series_of(ep)[0], fmt, STAGES, ep)}
            if a.id not in known:
                print(f"✗ no such question: {a.id} (this episode's questions: {', '.join(sorted(known)) or 'none'})")
                return 2
            if not a.text.strip():
                print("✗ the answer is empty")
                return 2
            p = ep / ANSWERS
            got = read_answers(p)
            got[a.id] = {"answer": a.text.strip(), "lines_hash": lines_hash(doc, fmt),
                         "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
            p.write_text(json.dumps(got, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"recorded {a.id}")
            return 0
        out = run(a.episode, a.stage)
    except ConfigError as e:
        print(f"✗ {e}")
        return 2
    show(out)
    print("all passed" if out["ok"] else "some items failed")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
