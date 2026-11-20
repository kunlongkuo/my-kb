"""tools/config/s2f_config.py。"""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/config"))
import s2f_config  # noqa: E402

SCRIPT = REPO / "tools/config/s2f_config.py"


def write(tmp_path, data, name="config.json"):
    p = tmp_path / name
    p.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def test_missing_file_changes_nothing(tmp_path):
    env = {"X": "1"}
    assert s2f_config.read(tmp_path / "nope.json") == {} and s2f_config.read(None) == {}
    assert s2f_config.fill(env, s2f_config.read(tmp_path / "nope.json")) == [] and env == {"X": "1"}


def test_environment_wins_and_empty_string_is_filled():
    env = {"S2F_EXPORT_CRF": "20", "S2F_SCRIBE_MODEL": ""}
    done = s2f_config.fill(env, {"S2F_EXPORT_CRF": "26", "S2F_SCRIBE_MODEL": "scribe_v2"})
    assert env == {"S2F_EXPORT_CRF": "20", "S2F_SCRIBE_MODEL": "scribe_v2"} and done == ["S2F_SCRIBE_MODEL"]


@pytest.mark.parametrize("new,old", sorted(s2f_config.OLD_NAMES.items()))
def test_old_name_in_the_environment_is_not_overridden(new, old):
    env = {old: "/old"}
    assert s2f_config.fill(env, {new: "/from/config"}) == [] and env == {old: "/old"}


def test_paths_expand_home_and_values_stay():
    env = {}
    s2f_config.fill(env, {"S2F_QWEN_TTS_DIR": "~/voice", "S2F_SCORE_WORK": "~/w", "S2F_YT_PYTHON": "~/py", "TP_ORIGINAL": "~x"})
    home = str(Path.home())
    assert env == {"S2F_QWEN_TTS_DIR": f"{home}/voice", "S2F_SCORE_WORK": f"{home}/w", "S2F_YT_PYTHON": f"{home}/py",
                   "TP_ORIGINAL": "~x"}


def test_numbers_become_strings_and_wrong_types_are_skipped():
    env = {}
    done = s2f_config.fill(env, {"S2F_EXPORT_CRF": 24, "S2F_TP_IDLE_MIN": 0, "S2F_VE_HEADED": True, "TP_ASPECT": None,
                                 "TP_GENDER": ["f"], "TP_ORIGINAL": {"a": 1}, "S2F_SCRIBE_MODEL": ""})
    assert env == {"S2F_EXPORT_CRF": "24", "S2F_TP_IDLE_MIN": "0"} and done == ["S2F_EXPORT_CRF", "S2F_TP_IDLE_MIN"]


def test_unknown_keys_and_secrets_are_never_filled():
    env = {}
    s2f_config.fill(env, {"GROQ_API_KEY": "k", "ELEVENLABS_API_KEY": "k", "YT_ACCOUNT": "x", "S2F_CONFIG": "/x",
                          "S2F_TEST_FONT": "/f", "NOT_A_KEY": "1"})
    assert env == {}
    assert not any("KEY" in k for k in s2f_config.KEYS) and "YT_ACCOUNT" not in s2f_config.KEYS


def test_empty_file_is_an_empty_config(tmp_path):
    assert s2f_config.read(write(tmp_path, "")) == {} and s2f_config.read(write(tmp_path, "  \n")) == {}


def test_broken_file_names_the_file(tmp_path):
    for bad in ("{not json", "[1, 2]", '"text"'):
        p = write(tmp_path, bad)
        with pytest.raises(s2f_config.ConfigError) as e:
            s2f_config.read(p)
        assert str(p) in str(e.value)


def test_config_path_follows_S2F_CONFIG(tmp_path):
    assert s2f_config.config_path({}, tmp_path) == tmp_path / ".config/script2film/config.json"
    assert s2f_config.config_path({"S2F_CONFIG": "none"}, tmp_path) is None
    assert s2f_config.config_path({"S2F_CONFIG": str(tmp_path / "other.json")}, tmp_path) == tmp_path / "other.json"


def test_export_is_safe_to_eval(tmp_path):
    folder = tmp_path / f"a b/it's $(touch {tmp_path}/pwned)"
    folder.mkdir(parents=True)
    cfg = write(tmp_path, {"S2F_ASSETS_LOCAL": str(folder), "S2F_EXPORT_CRF": 24, "NOT_A_KEY": "$(touch /x)"})
    env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "S2F_CONFIG": str(cfg)}
    cmd = f'eval "$({sys.executable} {SCRIPT} --export)"; printf %s "$S2F_ASSETS_LOCAL|$S2F_EXPORT_CRF"'
    r = subprocess.run(["zsh", "-c", cmd], env=env, capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout == f"{folder}|24", r.stderr
    assert not (tmp_path / "pwned").exists()
    out = subprocess.run([sys.executable, str(SCRIPT), "--export"], env=env, capture_output=True, text=True).stdout
    assert "NOT_A_KEY" not in out and all(line.startswith("export S2F_") for line in out.splitlines())


def test_export_skips_what_the_environment_already_has(tmp_path):
    cfg = write(tmp_path, {"S2F_QWEN_TTS_DIR": "/c", "S2F_EXPORT_CRF": 24})
    env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "S2F_CONFIG": str(cfg), "QWEN_TTS_DIR": "/old"}
    out = subprocess.run([sys.executable, str(SCRIPT), "--export"], env=env, capture_output=True, text=True).stdout
    assert out == "export S2F_EXPORT_CRF=24\n"


def test_show_names_the_source(tmp_path):
    cfg = write(tmp_path, {"S2F_EXPORT_CRF": 26})
    env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "S2F_CONFIG": str(cfg), "S2F_QWEN_TTS_DIR": "/tmp"}
    out = subprocess.run([sys.executable, str(SCRIPT), "--show"], env=env, capture_output=True, text=True).stdout
    rows = {line.split()[0]: line for line in out.splitlines()[1:]}
    assert rows["S2F_QWEN_TTS_DIR"].split()[1] == "env" and "/tmp" in rows["S2F_QWEN_TTS_DIR"]
    assert rows["S2F_EXPORT_CRF"].split()[1] == "config" and "26" in rows["S2F_EXPORT_CRF"]
    assert rows["S2F_WHISPER_CPP_MODEL"].split()[1] == "unset"


def test_broken_config_stops_the_command(tmp_path):
    cfg = write(tmp_path, "{broken")
    env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "S2F_CONFIG": str(cfg)}
    r = subprocess.run([sys.executable, str(SCRIPT), "--show"], env=env, capture_output=True, text=True)
    assert r.returncode == 2 and str(cfg) in r.stderr


def test_load_reads_the_file_once(tmp_path, monkeypatch):
    cfg = write(tmp_path, {"S2F_SCRIBE_MODEL": "m1"})
    monkeypatch.setenv("S2F_CONFIG", str(cfg))
    monkeypatch.delenv("S2F_SCRIBE_MODEL", raising=False)
    monkeypatch.setattr(s2f_config, "_LOADED", False)
    s2f_config.load()
    assert os.environ["S2F_SCRIBE_MODEL"] == "m1"
    cfg.write_text("{broken", encoding="utf-8")
    s2f_config.load()                                   # 第二次不讀檔：壞掉的內容不會讓它退出
    assert os.environ["S2F_SCRIBE_MODEL"] == "m1"
    monkeypatch.delenv("S2F_SCRIBE_MODEL")


def test_load_exits_2_on_a_broken_file(tmp_path, monkeypatch):
    monkeypatch.setenv("S2F_CONFIG", str(write(tmp_path, "{broken")))
    monkeypatch.setattr(s2f_config, "_LOADED", False)
    with pytest.raises(SystemExit) as e:
        s2f_config.load()
    assert e.value.code == 2


def test_tests_do_not_read_this_machines_config():
    """根 conftest.py 設了 S2F_CONFIG=none：這台機器的設定檔不會影響測試（從根目錄或子資料夾跑都一樣）。"""
    assert os.environ.get("S2F_CONFIG") == "none"


READER_GREP = ["git", "grep", "-l", "-E", "(S2F_[A-Z0-9_]+|TP_(ORIGINAL|HEADLESS|AUDIO_DIR|PROFILE|ASPECT|GENDER))", "--",
               "*.py", ":!*/tests/*", ":!*test_*", ":!openspec", ":!tools/config", ":!tools/doctor",
               ":!skills/ve-director/doc/formats", ":!*conftest.py"]


def readers():
    out = subprocess.run(READER_GREP, cwd=REPO, capture_output=True, text=True, check=True).stdout
    return [REPO / line for line in out.splitlines() if line]


def test_every_reader_loads():
    """每支讀設定的程式（內文出現 S2F_* 或六個 TP_* 名字的 .py）最前面都是那三行，而且 parents[N] 指得到這個倉庫。
    例外只有 formats/ 底下的起手模板：它是複製出去用的，用自己的 find_s2f() 找倉庫（tasks T3）。"""
    files = readers()
    assert len(files) >= 24, [str(f) for f in files]
    for f in files:
        body = ast.parse(f.read_text(encoding="utf-8")).body
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
            body = body[1:]                                                # docstring
        while body and isinstance(body[0], ast.ImportFrom) and body[0].module == "__future__":
            body = body[1:]
        n = len(f.relative_to(REPO).parts) - 1
        want = ["import sys as _sys, pathlib as _pl",
                f"_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[{n}] / 'tools/config'))",
                "import s2f_config", "s2f_config.load()"]
        assert [ast.unparse(x) for x in body[:4]] == want, f
        assert (f.resolve().parents[n] / "tools/config/s2f_config.py").exists(), f


def test_repo_python_only_for_repo_scripts_outside_any_venv(tmp_path):
    """倉庫有 .venv 而用系統 python3 跑倉庫裡的程式時才換直譯器（s2f-4a-install D1）。"""
    repo = tmp_path / "repo"
    (repo / "tools/x").mkdir(parents=True)
    script = repo / "tools/x/run.py"
    script.write_text("")
    f = s2f_config.repo_python
    assert f("/sys", "/sys", str(script), repo, {}) is None                      # 沒有 .venv：照舊
    (repo / ".venv/bin").mkdir(parents=True)
    py = repo / ".venv/bin/python"
    py.write_text("")
    assert f("/sys", "/sys", str(script), repo, {}) == py.resolve().parent / "python"
    assert f("/some/venv", "/sys", str(script), repo, {}) is None                # 已經在某個虛擬環境裡（.venv、配音的、uv 的）
    assert f("/sys", "/sys", None, repo, {}) is None                             # python3 -c、互動模式
    assert f("/sys", "/sys", str(tmp_path / "site-packages/pytest/__main__.py"), repo, {}) is None   # python3 -m pytest
    assert f("/sys", "/sys", str(repo / ".venv/bin/tool.py"), repo, {}) is None
    assert f("/sys", "/sys", str(script), repo, {"S2F_NO_VENV": "1"}) is None


def test_load_does_not_swap_python_under_pytest():
    """測試是 python3 -m pytest 跑的：__main__ 不是倉庫裡的程式檔，load() 不該把測試行程換掉。"""
    main = sys.modules["__main__"]
    assert s2f_config.repo_python(sys.prefix, sys.prefix, getattr(main, "__file__", None), s2f_config.REPO.parent / "nowhere", {}) is None



def test_runnable_scripts_load_config_before_third_party_imports():
    """可直接執行的程式要先 s2f_config.load()（換用 .venv）才能載入 pip 裝的套件，否則系統 python3 會 ModuleNotFoundError。"""
    import re
    repo = Path(__file__).resolve().parents[3]
    third = re.compile(r"^(?:import|from) (numpy|PIL|soundfile|opencc|fontTools|playwright)\b", re.M)
    bad = []
    for root in ("tools", "skills"):
        for p in (repo / root).rglob("*.py"):
            rel = p.relative_to(repo).as_posix()
            if "/tests/" in rel or "node_modules" in rel or p.name.startswith("test_") or "/.venv/" in rel:
                continue
            s = p.read_text(encoding="utf-8")
            m = third.search(s)
            if not m or '__name__ == "__main__"' not in s:
                continue
            c = s.find("s2f_config.load()")
            if c < 0 or c > m.start():
                bad.append(rel)
    assert not bad, bad
