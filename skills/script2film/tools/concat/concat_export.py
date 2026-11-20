"""Concat 出片的唯一入口：匯出 → 後處理 → 寫剪接用檔指紋 → 成片基本體檢（tools/nightly/film_check.py）。

所有出片腳本（plan2concat_mcp、drama_cut，以及各專案自己的組裝腳本）都呼叫 export()，不自己寫
export_start／export_wait 迴圈；tools/concat/test_single_export.py 守著這一條。這樣出片就一定體檢，新系列不會忘。

  from concat_export import export, add_no_check, parse_no_check, FilmCheckFailed
  ap = argparse.ArgumentParser(); add_no_check(ap); a = ap.parse_args(); skips = parse_no_check(ap, a.no_check)
  final = export(client, proj, out, post=lambda p: (loudnorm(p), p)[1], ep=<集資料夾>, inputs=[...], no_check=skips)

不想檢某項：--no-check <代號>:<原因>（可給好幾次；代號 all＝整個不檢）。代號表在 film_check.ITEMS。每一筆都記到
<集>/nightly/checklist_skips.jsonl（step 是 export），和 --skip-checklist 同一本；整個不檢的片沒有體檢紀錄，上傳時會被擋。
<片名>.inputs.json（指紋）只在這裡寫：檢查程式只讀，過期的片重跑檢查照樣不過。
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py（S2F_EXPORT_CRF 可寫在設定檔）
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / 'tools/config'))
import s2f_config; s2f_config.load()
import datetime, json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "nightly"))
import film_check  # noqa: E402

CODES = (*film_check.ITEMS, "all")


class FilmCheckFailed(RuntimeError):
    def __init__(self, video, result):
        super().__init__(f"film check failed: {video}")
        self.video, self.result = video, result


def export_crf():
    """成片的壓縮程度（x264 crf）：預設 24，環境變數 S2F_EXPORT_CRF 可改（16–32 的整數，其他值照預設）。
    2026-11-15 實測一集長片（6 分 38 秒、顆粒 3）：crf 20 是 214.6 MB，crf 24 是 135.7 MB，兩支互比 SSIM 0.990。"""
    v = os.environ.get("S2F_EXPORT_CRF", "")
    return int(v) if v.isdigit() and 16 <= int(v) <= 32 else 24


def add_no_check(ap):
    ap.add_argument("--no-check", action="append", default=[], metavar="ITEM:REASON",
                    help=f"skip one film-check item ({', '.join(CODES)}; all = no check at all) and say why; repeatable; "
                         "logged in <episode>/nightly/checklist_skips.jsonl")


def parse_no_check(ap, values):
    """['black_mid:原因', …] → [('black_mid', '原因'), …]；代號不在表上或原因空白：ap.error（exit 2）。"""
    out = []
    for v in values or []:
        code, _, why = v.partition(":")
        if code.strip() not in CODES:
            ap.error(f"--no-check {v!r}: item must be one of {', '.join(CODES)}")
        if not why.strip():
            ap.error(f"--no-check {v!r}: give a reason after the colon")
        out.append((code.strip(), why.strip()))
    return out


def log_skips(ep, video, skips):
    d = Path(ep) / "nightly"
    d.mkdir(parents=True, exist_ok=True)
    at = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    with open(d / "checklist_skips.jsonl", "a", encoding="utf-8") as f:
        for code, why in skips:
            f.write(json.dumps({"at": at, "step": "export", "item": code, "reason": why, "video": str(video)},
                               ensure_ascii=False) + "\n")
            print(f"film check skipped: {code} ({why})")


def write_inputs(video, ep, inputs):
    """<片名>.inputs.json：剪接用檔的 SHA-256（相對於集資料夾；不在集資料夾底下的寫絕對路徑）。只記存在的檔。"""
    base = Path(ep).resolve()
    files = {}
    for p in inputs:
        p = Path(p).resolve()
        if p.is_file():
            try:
                key = str(p.relative_to(base))
            except ValueError:
                key = str(p)
            files[key] = film_check.sha256(p)
    rec = film_check.record_paths(video)[1]
    rec.write_text(json.dumps({"base": str(base), "files": files,
                               "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def export(client, proj, out, *, crf="default", post=None, ep=None, inputs=(), no_check=(), standard=None):
    """匯出 proj 到 out，跑 post(out)（回傳交付檔路徑；None 表示就是 out），寫指紋、體檢。回傳交付檔路徑。
    crf："default"＝export_crf()；None＝不帶（例如有顆粒的片在 loudnorm 才重編碼）；整數＝照給的。
    ep：集資料夾（指紋的基準、跳過紀錄、系列門檻都看它）；沒給就用交付檔所在資料夾。
    體檢不過丟 FilmCheckFailed（呼叫端照常 exit 1）；匯出失敗丟 RuntimeError。"""
    args = {"path": proj, "output": str(out)}
    if crf == "default":
        args["crf"] = export_crf()
    elif crf is not None:
        args["crf"] = int(crf)
    job = client.tool("export_start", **args)["job"]
    while True:
        st = client.tool("export_wait", job=job, timeoutSeconds=600)
        if st.get("state") in ("done", "failed"):
            break
    if st["state"] != "done":
        raise RuntimeError(f"Concat export failed: {json.dumps(st, ensure_ascii=False)[:400]}")
    final = Path((post(str(out)) if post else None) or out).resolve()
    ep = Path(ep).resolve() if ep else final.parent
    write_inputs(final, ep, inputs)
    if no_check:
        log_skips(ep, final, no_check)
    if any(code == "all" for code, _ in no_check):
        return str(final)
    std = standard or film_check.load_standard(ep)
    result = film_check.basic(str(final), standard=std, skip=[code for code, _ in no_check], sfx_bed=ep / "sfx/sfx_bed.wav", ep=ep)
    film_check.write_record(final, result)
    film_check.show(result)
    if not result["ok"]:
        raise FilmCheckFailed(final, result)
    print(f"film check passed: {final.name}")
    return str(final)
