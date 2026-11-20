"""夜跑進度紀錄：每步開始／結束各記一筆，中斷後照這份接續，早上的報告也從這裡產。

  python3 tools/nightly/state.py <集資料夾> start S1
  python3 tools/nightly/state.py <集資料夾> done|warn|fail S1 "說明"     # warn＝有替補或退路，片子照出
  python3 tools/nightly/state.py <集資料夾> set youtube_url https://youtu.be/...   # 報告要用的值
  python3 tools/nightly/state.py <集資料夾> show
"""
import json, sys, time
from pathlib import Path

STEPS = {"S1": "voice", "S2": "pick takes", "S3": "timing", "S4a": "VE shots", "S4b": "code shots", "S5": "host",
         "S6": "assembly", "S7": "film", "S8": "film check", "S9": "upload"}


def main():
    P, cmd = Path(sys.argv[1]).resolve(), sys.argv[2]
    f = P / "nightly/state.json"
    f.parent.mkdir(exist_ok=True)
    st = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"steps": {}, "values": {}}
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    if cmd == "show":
        for k, name in STEPS.items():
            s = st["steps"].get(k, {})
            print(f"{k:4} {name:10} {s.get('status', '-'):5} {s.get('end', s.get('start', '')):19} {s.get('note', '')}")
        return
    if cmd == "set":
        st["values"][sys.argv[3]] = sys.argv[4]
    else:
        step = sys.argv[3]
        assert step in STEPS, f"unknown step {step}"
        s = st["steps"].setdefault(step, {})
        if cmd == "start":
            s.update(status="run", start=now)
            s.pop("end", None)
        else:
            assert cmd in ("done", "warn", "fail"), cmd
            s.update(status=cmd, end=now, note=" ".join(sys.argv[4:]))
    f.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
