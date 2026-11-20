import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checklist  # noqa: E402


@pytest.fixture(autouse=True)
def no_questions(tmp_path_factory, monkeypatch, request):
    """預設沒有要作答的題目，其他測試才看得清楚自己那一項；標了 real_rules 的測試用倉庫裡真的 rules.json。"""
    if "real_rules" in request.keywords:
        return
    p = tmp_path_factory.mktemp("rules") / "rules.json"
    p.write_text(json.dumps({"rules": []}), encoding="utf-8")
    monkeypatch.setattr(checklist, "RULES", p)


def pytest_configure(config):
    config.addinivalue_line("markers", "real_rules: use the repository's rules.json instead of an empty one")
