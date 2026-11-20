"""yt_paths：YouTube 憑證資料夾的位置（不匯入 yt_upload，它要 Google 的套件）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yt_paths import SECRET_NAME, creds_dir  # noqa: E402


def put_secret(folder):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / SECRET_NAME).write_text("{}")


def test_env_var(tmp_path):
    assert creds_dir({"S2F_YT_DIR": "/x/new"}, tmp_path) == Path("/x/new")


def test_empty_env_var_falls_back_to_default(tmp_path):
    assert creds_dir({"S2F_YT_DIR": ""}, tmp_path) == tmp_path / ".config/script2film/youtube"


def test_default_location(tmp_path):
    put_secret(tmp_path / ".config/script2film/youtube")
    assert creds_dir({}, tmp_path) == tmp_path / ".config/script2film/youtube"


def test_other_folder_with_secret_is_not_read(tmp_path):
    """家目錄別的資料夾有用戶端檔、或環境裡只有不帶 S2F_ 的變數名，都不採用，一律回預設位置。"""
    put_secret(tmp_path / ".youtube")
    assert creds_dir({"YT_DIR": "/x/old"}, tmp_path) == tmp_path / ".config/script2film/youtube"


def test_neither_set_nor_present_uses_default(tmp_path):
    assert creds_dir({}, tmp_path) == tmp_path / ".config/script2film/youtube"
