"""preflight 環境變數列：必要的兩個（S2F_QWEN_TTS_DIR、S2F_WHISPER_CPP_MODEL）缺了就擋；配音照
新舊名規則（新名有設就只驗新名，沒設才看舊名 QWEN_TTS_DIR），轉錄模型沒有舊名，列名一律是新名。選用的 S2F_ASSETS_LOCAL：沒設通過、
有設但資料夾不在擋、有設且在通過。另測 concat_bin、yt_python、font_item。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2] / "checklist"
sys.path.insert(0, str(HERE))
from items import OPTIONAL_ENV, REPO, REQUIRED_ENV, concat_bin, env_items, font_item, yt_item, yt_python  # noqa: E402


def full_env(tmp_path):
    return {k: str(tmp_path) for k in REQUIRED_ENV + OPTIONAL_ENV}


def rows(environ):
    return {name: (ok, detail) for name, ok, detail in env_items(environ)}


def test_required_all_present_pass(tmp_path):
    r = rows(full_env(tmp_path))
    assert all(r[f"env {k}"][0] is True for k in REQUIRED_ENV + OPTIONAL_ENV)


def test_required_missing_fails(tmp_path):
    env = full_env(tmp_path)
    del env["S2F_QWEN_TTS_DIR"]
    r = rows(env)
    assert r["env S2F_QWEN_TTS_DIR"] == (False, "not set")
    assert r["env S2F_WHISPER_CPP_MODEL"][0] is True


def test_required_nonexistent_fails(tmp_path):
    env = full_env(tmp_path) | {"S2F_WHISPER_CPP_MODEL": str(tmp_path / "nope.bin")}
    assert rows(env)["env S2F_WHISPER_CPP_MODEL"][0] is False


def test_retired_mlx_folder_does_not_count(tmp_path):
    env = full_env(tmp_path) | {"S2F_MLX_WHISPER_DIR": str(tmp_path), "MLX_WHISPER_DIR": str(tmp_path)}
    del env["S2F_WHISPER_CPP_MODEL"]
    assert rows(env)["env S2F_WHISPER_CPP_MODEL"] == (False, "not set")


def test_assets_local_unset_passes(tmp_path):
    env = full_env(tmp_path)
    del env["S2F_ASSETS_LOCAL"]
    assert rows(env)["env S2F_ASSETS_LOCAL"] == (True, "not set: bundled assets only")
    assert rows(env | {"S2F_ASSETS_LOCAL": ""})["env S2F_ASSETS_LOCAL"] == (True, "not set: bundled assets only")


def test_assets_local_set_but_missing_fails(tmp_path):
    env = full_env(tmp_path) | {"S2F_ASSETS_LOCAL": str(tmp_path / "nope")}
    ok, detail = rows(env)["env S2F_ASSETS_LOCAL"]
    assert ok is False and "does not exist" in detail


def test_assets_local_set_and_present_passes(tmp_path):
    assert rows(full_env(tmp_path))["env S2F_ASSETS_LOCAL"] == (True, str(tmp_path))


def test_old_names_only_pass(tmp_path):
    env = {"QWEN_TTS_DIR": str(tmp_path), "S2F_WHISPER_CPP_MODEL": str(tmp_path), "S2F_ASSETS_LOCAL": str(tmp_path)}
    r = rows(env)
    assert all(r[f"env {k}"][0] is True for k in REQUIRED_ENV + OPTIONAL_ENV)
    assert "QWEN_TTS_DIR" in r["env S2F_QWEN_TTS_DIR"][1]


def test_new_names_only_pass(tmp_path):
    env = {"S2F_QWEN_TTS_DIR": str(tmp_path), "S2F_WHISPER_CPP_MODEL": str(tmp_path), "S2F_ASSETS_LOCAL": str(tmp_path)}
    r = rows(env)
    assert all(r[f"env {k}"] == (True, str(tmp_path)) for k in REQUIRED_ENV + OPTIONAL_ENV)


def test_new_name_missing_path_does_not_fall_back(tmp_path):
    env = full_env(tmp_path) | {"S2F_QWEN_TTS_DIR": str(tmp_path / "nope"), "QWEN_TTS_DIR": str(tmp_path)}
    assert rows(env)["env S2F_QWEN_TTS_DIR"] == (False, str(tmp_path / "nope"))


def test_none_set_fails_with_new_names(tmp_path):
    items = env_items({})
    assert [name for name, _, _ in items] == [f"env {k}" for k in REQUIRED_ENV + OPTIONAL_ENV]
    assert all(ok is False and detail == "not set" for _, ok, detail in items[:len(REQUIRED_ENV)])
    assert items[-1][1:] == (True, "not set: bundled assets only")
    assert REQUIRED_ENV == ("S2F_QWEN_TTS_DIR", "S2F_WHISPER_CPP_MODEL")
    assert OPTIONAL_ENV == ("S2F_ASSETS_LOCAL",)


def test_concat_bin_new_and_old_names():
    assert concat_bin({"S2F_CONCAT_BIN": "/x"}) == Path("/x")
    assert concat_bin({"CONCAT_BIN": "/y"}) == Path("/y")
    assert concat_bin({"S2F_CONCAT_BIN": "/x", "CONCAT_BIN": "/y"}) == Path("/x")
    assert concat_bin({}) == Path("/Applications/Concat.app/Contents/MacOS/concat")


def test_font_item_present(tmp_path):
    (tmp_path / "fonts").mkdir()
    (tmp_path / "fonts/A.ttf").write_bytes(b"x")
    assert font_item({"font": "Fam=fonts/A.ttf"}, tmp_path) == ("font Fam", True, str(tmp_path / "fonts/A.ttf"))


def test_font_item_missing_file(tmp_path):
    name, ok, detail = font_item({"font": "Fam=../x/B.ttf"}, tmp_path)
    assert (name, ok, detail) == ("font Fam", False, str(tmp_path / "../x/B.ttf"))


def test_font_item_no_field(tmp_path):
    assert font_item({"name": "x"}, tmp_path) is None


def test_yt_python_set(tmp_path):
    assert yt_python({"S2F_YT_PYTHON": str(tmp_path / "py")}) == tmp_path / "py"


def test_yt_python_default():
    assert yt_python({}) == REPO / "tools/youtube/.venv/bin/python"


def test_yt_item_missing_interpreter_is_a_failed_row_not_a_crash(tmp_path):
    ok, detail = yt_item(tmp_path / "no-such-python", tmp_path / "yt_upload.py")
    assert ok is False and "S2F_YT_PYTHON" in detail
