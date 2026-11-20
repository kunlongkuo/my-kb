"""早上的一頁報告：彙整 nightly/state.json、checklist_start.json（沒有就讀舊的 preflight.json）、check.json → nightly/report.html。

  python3 tools/nightly/report.py <集資料夾>

最上面一行：綠＝已上稿（排定公開或可按公開）／黃＝已上稿但有替補或退路／紅＝沒上稿（附原因）。
"""
import html, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from state import STEPS


def load(f):
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def main():
    P = Path(sys.argv[1]).resolve()
    N = P / "nightly"
    st, pre, chk = load(N / "state.json"), load(N / "checklist_start.json") or load(N / "preflight.json"), load(N / "check.json")
    steps, val = st.get("steps", {}), st.get("values", {})
    stats = {k: steps.get(k, {}).get("status", "-") for k in STEPS}
    uploaded = stats["S9"] in ("done", "warn")
    pub = N / "yt_publish_at.txt"   # 有排定時間的集才有這個檔；沒有就是不公開上稿
    at = pub.read_text().strip()[5:16].replace("-", "/").replace("T", " ") if pub.exists() else ""
    if not uploaded:
        bad = [f"{k} {STEPS[k]}: {steps[k].get('note', '')}" for k in STEPS if stats[k] == "fail"] or ["the run did not finish"]
        light, head = "#c0392b", "Red: not uploaded | " + "; ".join(bad)
    elif any(s == "warn" for s in stats.values()):
        light, head = "#d4a017", "Yellow: uploaded, " + (f"goes public automatically at {at}; a stand-in or fallback was used, see the yellow steps below, and if you are not happy cancel the schedule in Studio before then" if at else "not public; a stand-in or fallback was used, see the yellow steps below before deciding whether to publish")
    else:
        light, head = "#2e8b57", "Green: uploaded, " + (f"goes public automatically at {at}" if at else "not public; publish it after looking at the frame sheet")
    e = html.escape
    color = {"done": "#2e8b57", "warn": "#d4a017", "fail": "#c0392b", "run": "#888", "-": "#bbb"}
    rows = "".join(f"<tr><td>{k}</td><td>{STEPS[k]}</td><td style='color:{color[stats[k]]};font-weight:700'>{stats[k]}</td>"
                   f"<td>{e(steps.get(k, {}).get('start', ''))}</td><td>{e(steps.get(k, {}).get('end', ''))}</td>"
                   f"<td>{e(steps.get(k, {}).get('note', ''))}</td></tr>" for k in STEPS)
    checks = "".join(f"<li>{'✓' if x['ok'] else '✗'} {e(x['item'])}: {e(str(x['value']))}</li>" for x in chk.get("items", []))
    pre_bad = "".join(f"<li>{e(x['item'])} {e(x['detail'])}</li>" for x in pre.get("items", []) if not x["ok"])
    links = "".join(f"<li>{e(k)}: {f'<a href=\"{e(v)}\">{e(v)}</a>' if v.startswith('http') else e(v)}</li>" for k, v in val.items())
    sheet = "<img src='sheet.jpg' style='width:100%'>" if (N / "sheet.jpg").exists() else "<p>(no frame sheet)</p>"
    page = f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nightly report {e(P.name)}</title>
<style>body{{font-family:-apple-system,"PingFang TC",sans-serif;max-width:1100px;margin:0 auto;padding:16px;background:#fff;color:#222}}
.light{{color:#fff;padding:14px 18px;border-radius:8px;font-size:20px;font-weight:700}}table{{border-collapse:collapse;width:100%}}
td{{border-bottom:1px solid #eee;padding:6px 8px;font-size:14px;vertical-align:top}}</style>
<div class="light" style="background:{light}">{e(head)}</div>
<h2>Links and outputs</h2><ul>{links or '<li>(none)</li>'}</ul>
<h2>Steps</h2><table>{rows}</table>
<h2>Film check</h2><ul>{checks or '<li>(not run)</li>'}</ul>
{f'<h2>Failed start checks</h2><ul>{pre_bad}</ul>' if pre_bad else ''}
<h2>Frame sheet (each beat 0.15 s after its first word)</h2>{sheet}
"""
    (N / "report.html").write_text(page, encoding="utf-8")
    print(N / "report.html")


if __name__ == "__main__":
    main()
