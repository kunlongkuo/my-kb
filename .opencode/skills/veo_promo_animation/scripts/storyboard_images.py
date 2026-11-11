"""用 Codex（ChatGPT 額度）依序生成／修改分鏡構圖圖，可指定模型與思考程度。
需要已登入的 Codex CLI（或 Codex 桌面版內附的 codex.exe；可用環境變數 CODEX_EXE 指定）。
Codex 產圖會存到 ~/.codex/generated_images/，本腳本依修改時間收集。

生成：python storyboard_images.py --prompts prompts.json --out <資料夾> --model <模型> --effort <程度> [--only s01,s02]
修改：python storyboard_images.py --prompts edits.json --out <資料夾> --model ... --edit   （每項需有 "src" 底圖）
prompts.json：{"style": "共用風格（可省）", "scenes": {"s01": "畫面描述", ...}}
edits.json：  {"scenes": {"s02": {"src": "<底圖>", "prompt": "修改說明"}}}
輸出檔名：<時間>-<scene>.png（修改版為 <scene>v2、v3…）。同場景已有輸出就跳過（--force 重生）。
一次只跑一支（Codex 產圖以修改時間收集，平行執行會互相搶檔）。
"""
import argparse, json, shutil, subprocess, sys, tempfile, time
from datetime import datetime
from pathlib import Path

import glob, os


class ci:  # Codex 產圖的共用設定
    GENERATED_DIR = Path.home() / ".codex" / "generated_images"
    ASPECTS = {"landscape": "landscape (wide, about 3:2)", "portrait": "portrait (tall, about 2:3)", "square": "square (1:1)"}

    @staticmethod
    def find_codex():
        exe = os.environ.get("CODEX_EXE")
        if exe and Path(exe).exists():
            return exe
        if shutil.which("codex"):
            return shutil.which("codex")
        try:  # Windows：Codex 桌面版（Microsoft Store）
            loc = subprocess.run(["powershell", "-NoProfile", "-Command",
                                  "(Get-AppxPackage *OpenAI.Codex* | Sort-Object Version -Descending | Select-Object -First 1).InstallLocation"],
                                 capture_output=True, text=True, timeout=30).stdout.strip()
            if loc and (Path(loc) / "app" / "resources" / "codex.exe").exists():
                return str(Path(loc) / "app" / "resources" / "codex.exe")
        except (OSError, subprocess.TimeoutExpired):
            pass
        sys.exit("找不到 Codex CLI：請安裝並登入 codex，或設定 CODEX_EXE。")


ap = argparse.ArgumentParser()
ap.add_argument("--prompts", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--model", required=True)
ap.add_argument("--effort", default="medium")
ap.add_argument("--only", default="")
ap.add_argument("--edit", action="store_true")
ap.add_argument("--force", action="store_true")
ap.add_argument("--timeout", type=int, default=600)
a = ap.parse_args()

cfg = json.load(open(a.prompts, encoding="utf-8"))
style = cfg.get("style", "")
out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
only = set(x for x in a.only.split(",") if x)
codex = ci.find_codex()

for sid, item in cfg["scenes"].items():
    if only and sid not in only:
        continue
    if a.edit:
        n = 2
        while list(out.glob(f"*-{sid}v{n}.png")):
            n += 1
        tag, src, prompt = f"{sid}v{n}", item["src"], item["prompt"]
    else:
        tag, src, prompt = sid, None, item if isinstance(item, str) else item["prompt"]
        if list(out.glob(f"*-{sid}.png")) and not a.force:
            print(sid, "已有，略過")
            continue
    text = prompt + ("\n\n" + style if style and not a.edit else "")
    lines = [f"Use your image generation tool to create 1 image(s).",
             "Do not write code, do not edit any files, and do not run shell commands."]
    if src:
        lines.append("Use the attached image(s) as the base/reference and apply the requested changes.")
    lines += [f"Aspect ratio: {ci.ASPECTS['landscape']}.", "Image request (follow it faithfully; render any quoted text exactly):",
              text, "When done, reply only with DONE."]
    cmd = [codex, "exec", "--skip-git-repo-check", "-s", "read-only", "-C", tempfile.gettempdir(),
           "-m", a.model, "-c", f'model_reasoning_effort="{a.effort}"']
    if src:
        cmd += ["-i", str(Path(src).resolve())]
    cmd.append("-")
    started = time.time() - 1
    try:
        subprocess.run(cmd, input="\n".join(lines), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=a.timeout)
    except subprocess.TimeoutExpired:
        print(sid, "逾時")
        continue
    new = sorted((p for p in ci.GENERATED_DIR.rglob("*.png") if p.stat().st_mtime >= started), key=lambda p: p.stat().st_mtime)
    if not new:
        print(sid, "沒有產生圖片（額度、登入或被拒）")
        continue
    dst = out / f"{datetime.now():%Y%m%d-%H%M%S}-{tag}.png"
    shutil.copy2(new[-1], dst)
    print(sid, "->", dst, flush=True)
