"""GSAP 本機載入、失敗時印原因。"""
import stat
import subprocess
import sys
from pathlib import Path

import pytest

DOC = Path(__file__).resolve().parents[1]
REPO = DOC.parents[2]
sys.path.insert(0, str(DOC / "scripts"))
import doc_common  # noqa: E402

LOCAL = '<script src="gsap.min.js"></script>'


def test_pages_load_gsap_from_their_own_folder():
    for f in ("lib/template.html", "scripts/doc_cut.py", "tests/fixtures/shell_no_bgm.html"):
        assert (DOC / f).read_text(encoding="utf-8").count(LOCAL) == 1, f


def test_no_cdn_left_in_code():
    if not (REPO / ".git").exists():
        pytest.skip("不是 git 倉庫")
    r = subprocess.run(["git", "grep", "-n", "-I", "-e", "cdnjs", "--", "skills", "tools", ":!*test_gsap_local.py"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.stdout == "", r.stdout


def test_gsap_is_copied_to_all_three_page_folders():
    code = (DOC / "scripts/doc_code.py").read_text(encoding="utf-8")
    cut = (DOC / "scripts/doc_cut.py").read_text(encoding="utf-8")
    assert 'shutil.copy(gsap_file(), out / "gsap.min.js")' in code            # code_<theme>/<beat>/
    assert 'shutil.copy(gsap_file(), S / "gsap.min.js")' in cut               # shell_<theme>/
    assert '"copy": ["index.html", "gsap.min.js", ' in cut                    # → cut_<theme>/ (tools/assemble copy_shell)


def test_gsap_file_points_into_node_modules_and_says_npm_ci_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(doc_common, "REPO", tmp_path)
    with pytest.raises(SystemExit) as e:
        doc_common.gsap_file()
    assert "npm ci" in str(e.value)
    f = tmp_path / "node_modules/gsap/dist/gsap.min.js"
    f.parent.mkdir(parents=True)
    f.write_text("x", encoding="utf-8")
    assert doc_common.gsap_file() == f


def test_log_tail(tmp_path):
    log = tmp_path / "x.log"
    log.write_text("\n".join(f"line {i}" for i in range(1, 13)) + "\n\n  \n", encoding="utf-8")
    assert doc_common.log_tail(log).splitlines() == [f"line {i}" for i in range(3, 13)]
    assert doc_common.log_tail(log, 2) == "line 11\nline 12"
    assert doc_common.log_tail(tmp_path / "nope.log") == ""


def test_render_failures_print_the_end_of_the_log():
    assert 'render failed: {log}\\n{log_tail(log)}' in (DOC / "scripts/doc_code.py").read_text(encoding="utf-8")
    assert "log_tail(o / 'render.log')" in (DOC / "scripts/doc_cut.py").read_text(encoding="utf-8")


def fake_cli(tmp_path, monkeypatch, body):
    """A fake whisper-cli (shell script) plus a model file and a silent input; returns the input path."""
    cli = tmp_path / "whisper-cli"
    cli.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    cli.chmod(cli.stat().st_mode | stat.S_IXUSR)
    (tmp_path / "model.bin").write_bytes(b"")
    monkeypatch.setenv("S2F_WHISPER_CLI", str(cli))
    monkeypatch.setenv("S2F_WHISPER_CPP_MODEL", str(tmp_path / "model.bin"))
    wav = tmp_path / "a.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "0.2", str(wav)], check=True)
    return wav


# 假 whisper-cli：每個 -f 檔旁寫一份 -ojf JSON（含特殊 token、空白 token、英文 BPE 片段、一個沒有 DTW 時間的 token）
FAKE_JSON = r"""for a; do case "$prev" in -f) cat > "$a.json" <<'J'
{"transcription": [{"text": " Hello world", "offsets": {"from": 0, "to": 2000}, "tokens": [
 {"text": "[_BEG_]", "offsets": {"from": 0, "to": 0}, "t_dtw": -1},
 {"text": " Hel", "offsets": {"from": 0, "to": 300}, "t_dtw": 50},
 {"text": "lo", "offsets": {"from": 300, "to": 600}, "t_dtw": 80},
 {"text": " ", "offsets": {"from": 600, "to": 700}, "t_dtw": 100},
 {"text": " world", "offsets": {"from": 700, "to": 1500}, "t_dtw": -1}]}]}
J
printf ' Hello\n world\n' > "$a.txt";; esac; prev="$a"; done
"""


def test_local_asr_failure_shows_the_transcribers_stderr(tmp_path, monkeypatch):
    wav = fake_cli(tmp_path, monkeypatch, "echo 'boom: model missing' >&2\nexit 3\n")
    with pytest.raises(SystemExit) as e:
        doc_common.local_asr([wav], "zh")
    assert "exit 3" in str(e.value) and "boom: model missing" in str(e.value)


def test_local_asr_missing_model_file_stops(tmp_path, monkeypatch):
    wav = fake_cli(tmp_path, monkeypatch, "exit 0\n")
    monkeypatch.setenv("S2F_WHISPER_CPP_MODEL", str(tmp_path / "nope.bin"))
    with pytest.raises(SystemExit) as e:
        doc_common.local_asr([wav], "en")
    assert "does not exist" in str(e.value)


def test_local_asr_text(tmp_path, monkeypatch):
    wav = fake_cli(tmp_path, monkeypatch, FAKE_JSON)
    assert doc_common.local_asr([wav], "en") == {wav: "Hello world"}


def test_local_asr_words_from_dtw(tmp_path, monkeypatch, capsys):
    """Special tokens dropped, a bare space only ends a word, BPE pieces joined; start = t_dtw / 100, end = next start;
    a token without DTW (-1) falls back to its offsets with one warning."""
    wav = fake_cli(tmp_path, monkeypatch, FAKE_JSON)
    seg = doc_common.local_asr([wav], "en", words=True)[wav]["segments"][0]
    assert (seg["start"], seg["end"]) == (0.0, 2.0)
    assert seg["words"] == [{"word": " Hello", "start": 0.5, "end": 1.0}, {"word": " world", "start": 0.7, "end": 2.0}]
    assert "no DTW word times" in capsys.readouterr().err


def test_local_asr_runs_with_dtw_and_no_flash_attention(tmp_path, monkeypatch):
    """DTW is off whenever flash attention is on, so word mode must pass -dtw with -nfa; one run for every file."""
    log = tmp_path / "args.txt"
    wav = fake_cli(tmp_path, monkeypatch, f'echo "$@" >> {log}\n' + FAKE_JSON)
    doc_common.local_asr([wav, wav], "zh", words=True)
    args = log.read_text().splitlines()
    assert len(args) == 1 and "-dtw large.v3.turbo" in args[0] and "-nfa" in args[0] and args[0].count("-f ") == 2


def test_a_failed_render_prints_what_the_renderer_said(tmp_path, monkeypatch):
    """假的 HyperFrames（印一行到 stderr、exit 1）：doc_cut.render 停下來的訊息要帶著那一行，不只是 log 的路徑。"""
    import shutil
    if not shutil.which("node"):
        pytest.skip("沒有 node")
    pkg = tmp_path / "hf"
    pkg.mkdir()
    (pkg / "package.json").write_text('{"name": "hyperframes", "bin": "cli.js"}', encoding="utf-8")
    (pkg / "cli.js").write_text('console.error("boom: chrome did not start"); process.exit(1);\n', encoding="utf-8")
    monkeypatch.setenv("S2F_HF_BIN", str(pkg))
    import doc_cut
    o = tmp_path / "cut"
    o.mkdir()
    with pytest.raises(SystemExit) as e:
        doc_cut.render(o)
    assert "render.log" in str(e.value) and "boom: chrome did not start" in str(e.value)
