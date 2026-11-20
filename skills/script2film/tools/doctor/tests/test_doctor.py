"""tools/doctor/doctor.py。"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/doctor"))
import doctor  # noqa: E402

SCRIPT = REPO / "tools/doctor/doctor.py"


def tool(tmp_path, name, venv=True):
    d = tmp_path / name
    (d / ".venv/bin").mkdir(parents=True)
    if venv:
        (d / ".venv/bin/python").write_text("")
    return d


def test_system_packages_ffmpeg_node():
    assert doctor.check_system("Darwin", "arm64")["status"] == "ok"
    assert doctor.check_system("Darwin", "x86_64")["status"] == "fail" and doctor.check_system("Linux", "arm64")["status"] == "fail"
    assert doctor.check_packages([])["status"] == "ok"
    miss = doctor.check_packages(["opencc", "PIL"])
    assert miss["status"] == "fail" and "python3 -m venv .venv" in miss["fix"] and "requirements.txt" in miss["fix"]
    again = doctor.check_packages(["opencc"], has_venv=True)["fix"]   # .venv 已經有：只補裝，不再叫人建一次
    assert again.startswith(".venv/bin/python -m pip install -r requirements.txt") and "venv .venv" not in again
    assert doctor.check_ffmpeg("/x/ffmpeg", "/x/ffprobe", " V..... libx264  H.264")["status"] == "ok"
    assert doctor.check_ffmpeg(None, "/x/ffprobe", "")["status"] == "fail"
    assert "libx264" in doctor.check_ffmpeg("/x/ffmpeg", "/x/ffprobe", "no encoders")["detail"]
    assert doctor.check_node("v22.3.0\n", 22)["status"] == "ok" and doctor.check_node("v20.1.0", 22)["status"] == "fail"
    assert doctor.check_node(None, 22)["detail"] == "node not found" and doctor.check_node("garbage", 22)["status"] == "fail"


def test_hyperframes_and_render_browser(tmp_path):
    assert doctor.check_hyperframes(tmp_path)["status"] == "ok" and doctor.check_hyperframes(None)["status"] == "fail"
    assert doctor.check_render_browser({}, tmp_path)["status"] == "fail"
    shell = tmp_path / ".cache/hyperframes/chrome/mac/chrome-headless-shell"
    shell.parent.mkdir(parents=True)
    shell.write_text("")
    assert doctor.check_render_browser({}, tmp_path)["status"] == "ok"
    assert doctor.check_render_browser({"HYPERFRAMES_BROWSER_PATH": str(shell)}, tmp_path / "other")["status"] == "ok"
    gone = doctor.check_render_browser({"HYPERFRAMES_BROWSER_PATH": "/nope"}, tmp_path)
    assert gone["status"] == "fail" and "/nope" in gone["fix"]


def test_playwright_browser(tmp_path):
    shell, ff = tmp_path / "chromium_headless_shell-1", tmp_path / "ffmpeg-1"
    gone = doctor.check_playwright_browser([shell, ff])
    assert gone["status"] == "fail" and str(shell) in gone["detail"] and gone["fix"] == doctor.PW_FIX
    assert doctor.PW_FIX.startswith(".venv/bin/python -m playwright install --only-shell chromium")
    shell.mkdir()
    (shell / "INSTALLATION_COMPLETE").write_text("")
    half = doctor.check_playwright_browser([shell, ff])                    # 錄影用的 ffmpeg 也要在
    assert half["status"] == "fail" and str(ff) in half["detail"] and str(shell) not in half["detail"]
    ff.mkdir()
    (ff / "INSTALLATION_COMPLETE").write_text("")
    assert doctor.check_playwright_browser([shell, ff])["status"] == "ok"
    unknown = doctor.check_playwright_browser(None, "the playwright package is not installed")
    assert unknown["status"] == "fail" and "not installed" in unknown["detail"] and unknown["fix"] == doctor.PW_FIX


def test_playwright_browser_follows_browsers_path(tmp_path):
    """真的問 Playwright（--dry-run，不下載）：位置跟著 PLAYWRIGHT_BROWSERS_PATH 走，裝完的標記在才算有。"""
    pw = tmp_path / "pw"
    pw.mkdir()
    rows_, r = run_env(tmp_path, PLAYWRIGHT_BROWSERS_PATH=str(pw))
    row_ = rows_["playwright browser"]
    assert row_["status"] == "fail" and str(pw) in row_["detail"] and "--only-shell chromium" in row_["fix"] and r.returncode == 1
    for p in row_["detail"].removeprefix("missing ").split(", "):
        Path(p).mkdir()
        (Path(p) / "INSTALLATION_COMPLETE").write_text("")
    rows_, _ = run_env(tmp_path, PLAYWRIGHT_BROWSERS_PATH=str(pw))
    assert rows_["playwright browser"]["status"] == "ok"


def test_tts_states(tmp_path):
    unset = doctor.check_tts({})
    assert unset["status"] == "fail" and "add" in unset["fix"] and "S2F_QWEN_TTS_DIR" in unset["detail"]
    gone = doctor.check_tts({"S2F_QWEN_TTS_DIR": str(tmp_path / "nope")})
    assert gone["status"] == "fail" and "to the correct path" in gone["fix"] and "S2F_QWEN_TTS_DIR" in gone["detail"]
    novenv = doctor.check_tts({"S2F_QWEN_TTS_DIR": str(tool(tmp_path, "novenv", venv=False))})
    assert novenv["status"] == "fail" and ".venv" in novenv["detail"]
    d = tool(tmp_path, "qwen")
    nomodel = doctor.check_tts({"S2F_QWEN_TTS_DIR": str(d)})
    assert nomodel["status"] == "fail" and "Hugging Face" in nomodel["fix"]
    (tmp_path / "_models" / doctor.QWEN_MODEL).mkdir(parents=True)
    assert doctor.check_tts({"S2F_QWEN_TTS_DIR": str(d)})["status"] == "ok"
    assert doctor.check_tts({"QWEN_TTS_DIR": str(d)})["status"] == "ok"                       # 舊名
    (tmp_path / "m2").mkdir()
    assert doctor.check_tts({"S2F_QWEN_TTS_DIR": str(d), "S2F_QWEN_TTS_MODELS": str(tmp_path / "m2")})["status"] == "fail"


def test_asr_states(tmp_path):
    none = lambda name: None
    found = lambda name: str(tmp_path / "whisper-cli")
    (tmp_path / "whisper-cli").write_text("")
    model = tmp_path / "ggml-large-v3-turbo.bin"
    assert doctor.check_asr({}, found)["status"] == "fail"
    assert "setup_voice.sh" in doctor.check_asr({}, found)["fix"] and "setup_voice.sh" in doctor.check_tts({})["fix"]
    old = doctor.check_asr({"S2F_MLX_WHISPER_DIR": str(tool(tmp_path, "mlx"))}, found)   # 只設了舊的 mlx 資料夾
    assert old["status"] == "fail" and "replaced by whisper.cpp" in old["detail"]
    assert "does not exist" in doctor.check_asr({"S2F_WHISPER_CPP_MODEL": str(model)}, found)["detail"]
    model.write_bytes(b"")
    no_cli = doctor.check_asr({"S2F_WHISPER_CPP_MODEL": str(model)}, none)
    assert no_cli["status"] == "fail" and "brew install whisper.cpp" in no_cli["fix"]
    assert doctor.check_asr({"S2F_WHISPER_CPP_MODEL": str(model)}, found)["status"] == "ok"
    via_env = doctor.check_asr({"S2F_WHISPER_CPP_MODEL": str(model), "S2F_WHISPER_CLI": str(tmp_path / "whisper-cli")}, none)
    assert via_env["status"] == "ok"


def test_requirements_file_matches_the_package_list():
    """requirements.txt 和 PACKAGES 是同一份：少一個，新機器照文件裝完會在用到的那一步才炸。"""
    lines = [x.strip() for x in (doctor.REPO / "requirements.txt").read_text(encoding="utf-8").splitlines()]
    assert sorted(x for x in lines if x and not x.startswith("#")) == sorted(doctor.PACKAGES.values())


def test_font_fix_is_two_commands_that_can_be_pasted():
    assert doctor.FONT_FIX.count("curl -L -o assets/fonts/") == 2 and "%5Bwght%5D" in doctor.FONT_FIX and "[wght]" not in doctor.FONT_FIX


def test_assets_disk(tmp_path):
    assert str(REPO / "assets") in doctor.check_assets({}, REPO)["detail"]   # 沒設 S2F_ASSETS 時看倉庫的 assets/（字型檔不在 git 裡，這裡不斷言通過；音效在 git 裡）
    assert doctor.check_assets({"S2F_ASSETS": str(tmp_path)}, REPO)["status"] == "fail"
    # 字型檔不在 git 裡：只有 manifest、沒有字型檔的資料夾（剛 clone 下來的樣子）不算通過，修法要說去哪裡拿
    (tmp_path / "fonts").mkdir(); (tmp_path / "sfx").mkdir()
    (tmp_path / "sfx/manifest.json").write_text("[]", encoding="utf-8")
    (tmp_path / "fonts/manifest.json").write_text('[{"id": "A", "file": "A.ttf"}]', encoding="utf-8")
    r = doctor.check_assets({"S2F_ASSETS": str(tmp_path)}, REPO)
    assert r["status"] == "fail" and "fonts/A.ttf" in r["detail"] and "google/fonts" in r["fix"]
    for bad in ("{not json", '{"file": "A.ttf"}', '[{"id": "A"}]'):   # 壞掉的 manifest：說是這個檔的問題，不叫人重新 clone
        (tmp_path / "fonts/manifest.json").write_text(bad, encoding="utf-8")
        r = doctor.check_assets({"S2F_ASSETS": str(tmp_path)}, REPO)
        assert r["status"] == "fail" and "cannot read" in r["detail"] and "manifest.json" in r["detail"] and "restore" in r["fix"], bad
    (tmp_path / "fonts/manifest.json").write_text('[{"id": "A", "file": "A.ttf"}]', encoding="utf-8")
    (tmp_path / "fonts/A.ttf").write_bytes(b"x")
    assert doctor.check_assets({"S2F_ASSETS": str(tmp_path)}, REPO)["status"] == "ok"
    # 選用字型沒下載不擋，也不算進數量
    (tmp_path / "fonts/manifest.json").write_text('[{"id": "A", "file": "A.ttf"}, {"id": "B", "file": "B.ttf", "optional": true}]', encoding="utf-8")
    r = doctor.check_assets({"S2F_ASSETS": str(tmp_path)}, REPO)
    assert r["status"] == "ok" and "fonts: 1" in r["detail"]
    (tmp_path / "fonts/manifest.json").write_text('[{"id": "A", "file": "A.ttf"}]', encoding="utf-8")
    # 音效隨倉庫附帶：manifest 列了但檔不在，修法是用 git 還原，不是下載字型
    (tmp_path / "sfx/manifest.json").write_text('[{"id": "s", "file": "ve-gen/s.mp3"}]', encoding="utf-8")
    r = doctor.check_assets({"S2F_ASSETS": str(tmp_path)}, REPO)
    assert r["status"] == "fail" and "sfx/ve-gen/s.mp3" in r["detail"] and "git checkout -- assets/sfx" in r["fix"]
    (tmp_path / "sfx/ve-gen").mkdir(); (tmp_path / "sfx/ve-gen/s.mp3").write_bytes(b"x")
    r = doctor.check_assets({"S2F_ASSETS": str(tmp_path)}, REPO)
    assert r["status"] == "ok" and "sounds: 1" in r["detail"]
    assert doctor.check_disk(100.0, 5)["status"] == "ok" and doctor.check_disk(1.2, 5)["status"] == "fail"


def test_config_item(tmp_path):
    p = tmp_path / "config.json"
    assert doctor.check_config(None, {})["status"] == "ok" and doctor.check_config(p, {})["status"] == "ok"     # 不存在算通過
    p.write_text("{}")
    good = {"S2F_QWEN_TTS_DIR": str(tmp_path), "S2F_EXPORT_CRF": 24,
            "S2F_SCORE_WORK": str(tmp_path / "new1"), "S2F_TP_PROFILE": str(tmp_path / "new2"),
            "S2F_SPEECHBRAIN_CACHE": str(tmp_path / "new3"), "S2F_YT_DIR": str(tmp_path / "new4")}   # newdir 類還不存在也通過
    assert doctor.check_config(p, good)["status"] == "ok"
    bad = doctor.check_config(p, {"NOPE": "1", "GROQ_API_KEY": "k", "S2F_EXPORT_CRF": [1], "S2F_QWEN_TTS_DIR": "/nonexistent",
                                  "S2F_YT_PYTHON": "/nonexistent/python"})
    assert bad["status"] == "fail"
    for word in ("NOPE: unknown key", "GROQ_API_KEY", "secrets.json", "S2F_EXPORT_CRF: the value must", "S2F_QWEN_TTS_DIR: /nonexistent does not exist",
                 "S2F_YT_PYTHON"):
        assert word in bad["detail"], word


def test_optional_items(tmp_path):
    assert doctor.check_concat(tmp_path / "nope")["status"] == "fail" and doctor.check_concat(tmp_path)["group"] == "concat"
    assert doctor.check_chrome(tmp_path)["status"] == "ok" and doctor.check_chrome(tmp_path / "x")["group"] == "ve"
    assert doctor.check_tp(tmp_path)["status"] == "ok" and doctor.check_tp(tmp_path / "x")["status"] == "fail"
    ve = doctor.check_ve(tmp_path)
    assert ve["status"] == "fail" and ve["group"] == "ve" and "S2F_VE_HEADED=1" in ve["fix"]
    (tmp_path / "Default").mkdir()
    (tmp_path / "Default" / "Cookies").write_bytes(b"x")
    assert doctor.check_ve(tmp_path)["status"] == "ok"
    py = tmp_path / "python"
    py.write_text("")
    assert doctor.check_youtube(py, tmp_path, "secret.json")["status"] == "fail"
    (tmp_path / "secret.json").write_text("")
    assert doctor.check_youtube(py, tmp_path, "secret.json")["status"] == "ok"
    assert doctor.check_youtube(tmp_path / "nope", tmp_path, "secret.json")["status"] == "fail"
    assert doctor.check_assets_local({})["group"] == "note" and doctor.check_assets_local({})["status"] == "fail"
    assert doctor.check_assets_local({"S2F_ASSETS_LOCAL": str(tmp_path)})["status"] == "ok"
    assert "to the correct path" in doctor.check_assets_local({"S2F_ASSETS_LOCAL": str(tmp_path / "x")})["fix"]


def test_secrets_permission_is_read_without_opening_the_file(tmp_path):
    p = tmp_path / "secrets.json"
    assert doctor.check_secrets(p)["status"] == "ok"                       # 沒有金鑰檔
    p.write_text("{this is not json and holds a secret")
    os.chmod(p, 0o644)
    bad = doctor.check_secrets(p)
    assert bad["status"] == "fail" and bad["fix"] == f"chmod 600 {p}" and "secret" not in bad["detail"].replace(str(p), "")
    os.chmod(p, 0o000)                                                     # 讀不了的檔也查得出權限：沒有開檔
    assert doctor.check_secrets(p)["status"] == "fail"
    os.chmod(p, 0o600)
    assert doctor.check_secrets(p)["status"] == "ok"


def rows(*pairs):
    return [doctor.row(f"n{i}", g, ok, "d", "fix it") for i, (g, ok) in enumerate(pairs)]


def test_exit_code_and_marks():
    assert doctor.exit_code(rows(("required", True), ("concat", False), ("note", False)), []) == 0
    assert doctor.exit_code(rows(("required", False)), []) == 1
    assert doctor.exit_code(rows(("required", True), ("concat", False)), ["concat"]) == 1
    assert doctor.exit_code(rows(("required", True), ("concat", False)), ["ve"]) == 0
    text = doctor.render(rows(("required", True), ("concat", False), ("note", False)), [])
    assert text.splitlines() == ["✓ n0  d", "－ n1  d", "   → fix it", "－ n2  d", "   → fix it", "✓ ready to go"]
    text = doctor.render(rows(("required", False), ("concat", False)), ["concat"])
    assert text.splitlines()[0] == "✗ n0  d" and text.splitlines()[2] == "✗ n1  d" and text.splitlines()[-1] == "✗ 2 to fix"


def run(tmp_path, *args, cfg=None):
    env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path)}
    if cfg is not None:
        p = tmp_path / "cfg.json"
        p.write_text(cfg, encoding="utf-8")
        env["S2F_CONFIG"] = str(p)
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)


def test_json_output_and_twenty_items(tmp_path):
    r = run(tmp_path, "--json")
    data = json.loads(r.stdout)
    assert len(data) == 20 and all(set(d) == {"name", "group", "status", "detail", "fix"} for d in data)
    assert [d["group"] for d in data].count("required") == 13
    assert {d["group"] for d in data} == {"required", "concat", "ve", "tp", "youtube", "note"}
    assert r.returncode == 1                                               # 空的家目錄：配音、轉錄一定缺


def test_broken_config_exits_2(tmp_path):
    r = run(tmp_path, cfg="{broken")
    assert r.returncode == 2 and "cfg.json" in r.stderr


def test_bad_arguments(tmp_path):
    for bad in (["--need", "nope"], ["--wat"], ["--need"], ["--need", ","]):
        assert run(tmp_path, *bad).returncode == 64, bad                   # 用法錯誤和「必要的項目有 ✗」（1）分開
    r = run(tmp_path, "--need", "concat,tp")
    assert r.returncode == 1 and r.stdout.splitlines()[-1].startswith("✗ ")


def run_env(tmp_path, **extra):
    env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "S2F_CONFIG": "none", **extra}
    r = subprocess.run([sys.executable, str(SCRIPT), "--json"], env=env, capture_output=True, text=True)
    return {d["name"]: d for d in json.loads(r.stdout)}, r


def test_hyperframes_uses_the_real_lookup(tmp_path):
    """S2F_HF_BIN 指到不存在的路徑時要是 ✗（程式實際渲染時會停在這裡），不能往上找到倉庫根的 package.json 就算過。"""
    rows_, _ = run_env(tmp_path, S2F_HF_BIN=str(REPO / "nope"))
    assert rows_["HyperFrames"]["status"] == "fail" and "S2F_HF_BIN" in rows_["HyperFrames"]["detail"]
    empty = tmp_path / "pkg"
    empty.mkdir()
    rows_, _ = run_env(tmp_path, S2F_HF_BIN=str(empty))                    # 資料夾在，但不是 HyperFrames 套件
    assert rows_["HyperFrames"]["status"] == "fail"


def test_missing_home_is_reported_not_a_traceback(tmp_path):
    rows_, r = run_env(tmp_path / "no" / "such" / "home")
    assert "Traceback" not in r.stderr and rows_["disk"]["status"] in ("ok", "fail") and len(rows_) == 20


def test_gsap_is_a_required_item(tmp_path):
    r = doctor.check_gsap(tmp_path)
    assert r["group"] == "required" and r["status"] == "fail" and "npm ci" in r["fix"]
    (tmp_path / "node_modules/gsap/dist").mkdir(parents=True)
    (tmp_path / "node_modules/gsap/dist/gsap.min.js").write_text("x", encoding="utf-8")
    assert doctor.check_gsap(tmp_path)["status"] == "ok"


def test_skip_voice_turns_only_those_two_failures_into_skipped(tmp_path):
    """--skip voice（CI 不裝配音模型）：配音、轉錄缺了是 skipped、不算失敗；其他必要項目缺了照樣是 1。"""
    base = [doctor.row("voice (TTS)", "required", False, "S2F_QWEN_TTS_DIR is not set", "fix"),
            doctor.row("transcription", "required", False, "S2F_WHISPER_CPP_MODEL is not set", "fix"),
            doctor.row("ffmpeg", "required", True, "d")]
    out = doctor.apply_skip(base, ["voice"])
    assert [r["status"] for r in out] == ["skipped", "skipped", "ok"] and out[0]["fix"] == ""
    assert doctor.exit_code(out, []) == 0
    text = doctor.render(out, []).splitlines()
    assert text[0].startswith("－ voice (TTS)  skipped (--skip voice): ") and text[-1] == "✓ ready to go (skipped: voice (TTS), transcription)"
    assert doctor.exit_code(doctor.apply_skip(base + [doctor.row("GSAP", "required", False, "d", "npm ci")], ["voice"]), []) == 1
    ok = [doctor.row("voice (TTS)", "required", True, "d")]
    assert doctor.apply_skip(ok, ["voice"]) == ok                          # 裝好了就照舊 ✓
    assert doctor.apply_skip(base, []) == base


def test_skip_voice_from_the_command_line(tmp_path):
    rows_ = {d["name"]: d for d in json.loads(run(tmp_path, "--skip", "voice", "--json").stdout)}
    assert rows_["voice (TTS)"]["status"] == "skipped" and rows_["transcription"]["status"] == "skipped"
    for bad in (["--skip"], ["--skip", "nope"], ["--skip", ","]):
        assert run(tmp_path, *bad).returncode == 64, bad
