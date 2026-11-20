"""vox-host 範本 make_doc_template.py 的 find_s2f()（s2f-naming D3）。範本一匯入就匯入 doc_lint、doc_build 並在目前資料夾
寫 doc.json，所以不匯入它：用 ast 取出 find_s2f 的定義，在只有 os、sys、Path、__file__ 的命名空間裡 exec。"""
import ast
import os
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "formats/vox-host/make_doc_template.py"


def load_find_s2f():
    tree = ast.parse(TEMPLATE.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "find_s2f")
    ns = {"os": os, "sys": sys, "Path": Path, "__file__": str(TEMPLATE)}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(TEMPLATE), "exec"), ns)
    return ns["find_s2f"]


def test_find_s2f_new_name_only(monkeypatch, tmp_path):
    monkeypatch.delenv("PROMPTSTUDIO_DIR", raising=False)
    monkeypatch.setenv("S2F_DIR", str(tmp_path))
    assert load_find_s2f()() == tmp_path


def test_find_s2f_old_name_only(monkeypatch, tmp_path):
    monkeypatch.delenv("S2F_DIR", raising=False)
    monkeypatch.setenv("PROMPTSTUDIO_DIR", str(tmp_path))
    assert load_find_s2f()() == tmp_path
