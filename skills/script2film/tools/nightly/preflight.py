"""起跑前檢查的舊入口：已改到 tools/checklist/checklist.py（三層、兩段的清單），這裡照跑開工段。

  python3 tools/nightly/preflight.py <集>/doc.json     等於  python3 tools/checklist/checklist.py run <集> --stage start

結果寫到 <集>/nightly/checklist_start.json，退出碼和清單相同。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "checklist"))
import checklist  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Old entry point for the start check, now tools/checklist/checklist.py (three layers, two stages); runs its start stage.\n\n"
                 "  python3 tools/nightly/preflight.py <episode>/doc.json     same as  "
                 "python3 tools/checklist/checklist.py run <episode> --stage start\n\n"
                 "Writes <episode>/nightly/checklist_start.json; the exit code is the checklist's.")
    print("moved to tools/checklist/checklist.py: running its start stage")
    sys.exit(checklist.main(["run", str(Path(sys.argv[1]).resolve().parent), "--stage", "start"]))
