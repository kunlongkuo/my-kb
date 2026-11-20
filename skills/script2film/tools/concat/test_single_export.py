"""出片只有一個入口：export_start 只能出現在 tools/concat/concat_export.py。
新的出片腳本若自己寫 Concat 匯出迴圈，就繞過了成片體檢（openspec film-check-all D2）；這裡擋住。
另外要掃的工作資料夾（放各專案組裝腳本的 repo）寫在 S2F_EXPORT_SCAN（用 os.pathsep 隔開）；沒設就只掃本 repo。
offenders() 也給別的 repo 自己的測試匯入使用。"""
import os
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ALLOWED = {REPO / "tools/concat/concat_export.py"}
CALL = re.compile(r"""["']export_start["']""")


def py_files(root, subdirs):
    for sub in subdirs:
        base = root / sub
        if base.is_dir():
            for p in base.rglob("*.py"):
                if "__pycache__" not in p.parts and ".venv" not in p.parts and not p.name.startswith("test_"):
                    yield p


def offenders(root, subdirs):
    return [str(p) for p in py_files(root, subdirs) if p.resolve() not in ALLOWED and CALL.search(p.read_text(encoding="utf-8", errors="ignore"))]


def test_promptstudio_has_one_export_entry():
    assert offenders(REPO, ["tools", "skills"]) == []


def test_extra_work_folders_have_no_own_export_loop():
    roots = [Path(x) for x in os.environ.get("S2F_EXPORT_SCAN", "").split(os.pathsep) if x]
    if not roots:
        pytest.skip("S2F_EXPORT_SCAN not set")
    assert [o for r in roots for o in offenders(r, ["."])] == []


def test_the_scan_finds_a_planted_loop(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/new_cut.py").write_text('job = c.tool("export_start", path=p, output=o)\n')
    assert offenders(tmp_path, ["tools"]) == [str(tmp_path / "tools/new_cut.py")]
