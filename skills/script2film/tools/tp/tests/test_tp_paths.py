"""tp_paths：TP 設定檔資料夾的新舊名順序與 serve 紀錄檔位置。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tp_paths import idle_expired, idle_minutes, last_use_file, profile_dir, serve_log  # noqa: E402


def test_profile_dir_new_name_only(tmp_path):
    assert profile_dir({"S2F_TP_PROFILE": "/x/new", "TP_PROFILE": ""}, tmp_path) == Path("/x/new")


def test_profile_dir_old_name_only(tmp_path):
    assert profile_dir({"TP_PROFILE": "/x/old"}, tmp_path) == Path("/x/old")


NEW = ".config/script2film/tp-profile"
OLD = ".cutline-profiles/tp"   # 舊版的預設位置


def test_profile_dir_default_is_the_new_folder(tmp_path):
    assert profile_dir({}, tmp_path) == tmp_path / NEW


def test_profile_dir_keeps_the_old_folder_when_only_it_exists(tmp_path):
    (tmp_path / OLD).mkdir(parents=True)
    assert profile_dir({}, tmp_path) == tmp_path / OLD


def test_profile_dir_new_folder_wins_when_both_exist(tmp_path):
    (tmp_path / OLD).mkdir(parents=True)
    (tmp_path / NEW).mkdir(parents=True)
    assert profile_dir({}, tmp_path) == tmp_path / NEW


def test_profile_dir_env_wins_over_both_folders(tmp_path):
    (tmp_path / OLD).mkdir(parents=True)
    assert profile_dir({"S2F_TP_PROFILE": "/x/new"}, tmp_path) == Path("/x/new")


def test_serve_log_default(tmp_path):
    assert serve_log({}, tmp_path) == tmp_path / ".config/script2film/tp_serve.log"


def test_serve_log_follows_the_old_folder(tmp_path):
    (tmp_path / OLD).mkdir(parents=True)
    assert serve_log({}, tmp_path) == tmp_path / ".cutline-profiles/tp_serve.log"


def test_last_use_file_sits_beside_the_profile(tmp_path):
    assert last_use_file({"S2F_TP_PROFILE": "/x/p/tp"}, tmp_path) == Path("/x/p/tp_last_use")


def test_idle_minutes():
    assert idle_minutes({}) == 10
    assert idle_minutes({"S2F_TP_IDLE_MIN": "3"}) == 3
    assert idle_minutes({"S2F_TP_IDLE_MIN": "0"}) == 0          # 不自動關
    assert idle_minutes({"S2F_TP_IDLE_MIN": "abc"}) == 10
    assert idle_minutes({"S2F_TP_IDLE_MIN": "-5"}) == 10


def test_idle_expired():
    assert idle_expired(1000 + 601, 1000, 10) is True
    assert idle_expired(1000 + 599, 1000, 10) is False
    assert idle_expired(10 ** 9, 0, 0) is False
