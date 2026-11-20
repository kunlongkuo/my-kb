"""Concat 執行檔位置（s2f-naming D6）：S2F_CONCAT_BIN 有設就用它，沒設才用舊名 CONCAT_BIN。"""
import importlib

import plan2concat_mcp


def test_concat_bin_new_and_old_name(monkeypatch):
    try:
        monkeypatch.delenv("CONCAT_BIN", raising=False)
        monkeypatch.setenv("S2F_CONCAT_BIN", "/x")
        assert importlib.reload(plan2concat_mcp).CONCAT == "/x"
        monkeypatch.delenv("S2F_CONCAT_BIN")
        monkeypatch.setenv("CONCAT_BIN", "/y")
        assert importlib.reload(plan2concat_mcp).CONCAT == "/y"
    finally:
        monkeypatch.undo()
        importlib.reload(plan2concat_mcp)
