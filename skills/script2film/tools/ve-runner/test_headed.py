"""S2F_VE_HEADED (s2f-naming D6): when it is set only it counts; the old name VE_HEADED is read only when it is not."""
import ve_runner
from ve_runner import headed, wait_for_enter


def test_headed_new_and_old_name():
    assert headed({"S2F_VE_HEADED": "1"}) is True
    assert headed({"VE_HEADED": "1"}) is True
    assert headed({"S2F_VE_HEADED": "0", "VE_HEADED": "1"}) is False


def test_wait_for_enter_only_with_a_window_and_a_terminal():
    assert wait_for_enter(True, True) is True
    assert [wait_for_enter(False, True), wait_for_enter(True, False), wait_for_enter(False, False)] == [False] * 3


def test_never_logged_in_is_a_profile_without_cookies(tmp_path):
    assert ve_runner.never_logged_in(tmp_path)
    (tmp_path / "Default").mkdir()
    assert ve_runner.never_logged_in(tmp_path)          # launch_browser writes Default/Preferences before Chrome runs
    (tmp_path / "Default" / "Cookies").write_bytes(b"x")
    assert not ve_runner.never_logged_in(tmp_path)
    assert "S2F_VE_HEADED=1" in ve_runner.LOGIN_HINT and "--login" in ve_runner.LOGIN_HINT


def test_headless_run_on_a_fresh_profile_stops_before_the_browser(tmp_path, monkeypatch):
    import argparse
    import pytest
    monkeypatch.setattr(ve_runner, "HERE", tmp_path)
    monkeypatch.setattr(ve_runner, "HEADED", False)
    monkeypatch.setattr(ve_runner, "sync_playwright", lambda: pytest.fail("the browser must not start"))
    with pytest.raises(SystemExit) as e:
        ve_runner._run(argparse.Namespace(inspect=False, login=True, runsheet=None), tmp_path)
    assert "--login" in str(e.value) and "S2F_VE_HEADED=1" in str(e.value)
