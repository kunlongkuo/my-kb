"""主持人分段一鍵做完：上傳音檔 → 送 TP 渲染 → 等 → 下載 → 驗長度。

  python3 tools/tp/tp_host.py <集資料夾> --prefix Ep01r2 [--look "Host shirt"] [--parts 1 3] [--timeout 30]

先跑 `python3 tools/tp/tp_browser.py serve`（背景，已登入的 profile）與 `doc_host.py split`（產 host/parts/partK.mp3）。
每段的 TP 名稱＝「<prefix> partK」（媒體庫音檔與成片同名）。可重跑：媒體庫已有就不再上傳、My Videos 已有就不再送，只等與下載。
下載到 host/parts/partK.mp4（舊檔先移成 .bak.mp4）；長度與音檔差超過 --tol 秒、或缺畫面／聲音就失敗。
退出碼 0＝全部下載且驗過；1＝失敗（訊息寫明哪段、哪一步）；2＝等超過 --timeout 分鐘。

實際操作學到的：
- 媒體庫資料夾要點文字「Audio」才打得開，點座標沒反應。
- 資料夾可用環境變數 TP_AUDIO_DIR 換（預設 Audio）。一個資料夾累積約 30 頁後，新上傳的音檔不再出現：
  在 Media Library 下新建一個資料夾，用這個變數改傳那裡。
- 建立流程會停在上一次的 Render 步驟（名稱欄還是上次的名字）：這時用 tp_swap.sh 換音檔與名稱；全新流程才用 tp_submit.sh。
- My Videos 卡片狀態是 pending → processing → 消失（＝完成），一段約 23 分鐘；下載＝卡片上第 2 顆按鈕。
- 同時渲染最多 5 段：超過的段落排隊，前面完成一段再送。
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import argparse, json, os, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tp_paths import serve_log  # noqa: E402
sys.path.insert(0, str(HERE.parent / "checklist"))
import checklist  # noqa: E402

AUDIO_DIR = os.environ.get("TP_AUDIO_DIR", "Audio")   # 媒體庫音檔資料夾（tp_submit.sh 讀同一個變數）
TOL_DEFAULT = 0.3   # 提議值（規範沒有）；首跑實測差 0.02 秒
MAX_ACTIVE = 5      # TP 同時渲染上限：第 6 段會停在 Human Video 送不出去（實測）


def tp(*a, timeout=60):
    r = subprocess.run([sys.executable, HERE / "tp_browser.py", *map(str, a)], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()


def ev(js):
    out = tp("eval", js)
    try:
        return json.loads(out.splitlines()[-1]) if out else None
    except json.JSONDecodeError:
        return out


def go(hash_, wait=4):
    ev(f"(()=>{{location.hash='{hash_}';return 1}})()")
    time.sleep(wait)


TP_LOGIN = ("✗ TP is on the login page: ask the user to log in themselves in the open TP window (never type the password for them), "
            "then rerun this command. The window closes itself after 10 minutes without a command (S2F_TP_IDLE_MIN); "
            "if it closed, run python3 tools/tp/tp_browser.py serve in the background again")


def leaf_texts(pattern):
    return ev("[...document.querySelectorAll('*')].filter(e=>e.offsetParent&&e.children.length===0&&"
              f"/{pattern}/.test(e.textContent.trim())).map(e=>e.textContent.trim())") or []


def tp_name(prefix):
    """The name TP shows for a file named <prefix>: underscores become spaces and the first letter is capitalised
    ("boba_emma" shows as "Boba emma"; 2026-11-18 a prefix with "_" uploaded fine but was never found in the media
    library). has() and card() compare with what TP shows, so the labels are built from this."""
    p = prefix.replace("_", " ")
    return p[:1].upper() + p[1:]


def has(label):
    return label.lower() in [t.lower() for t in leaf_texts(".")]


def card(label):
    """My Videos 上這個名稱的卡片（往上爬到整張卡，含左邊縮圖上的 processing 標籤；只取文字區會誤判完成）：{'text': 卡片文字, 'buttons': [[x, y], ...]}，沒有就 None。"""
    return ev(f"""(()=>{{const l=[...document.querySelectorAll('*')].find(e=>e.offsetParent&&e.children.length===0&&e.textContent.trim()==={json.dumps(label)});
      if(!l)return null;l.scrollIntoView({{block:'center'}});let c=l;for(let i=0;i<6&&c.querySelectorAll('button').length<2;i++)c=c.parentElement;while(c.parentElement&&c.parentElement.querySelectorAll('button').length===c.querySelectorAll('button').length)c=c.parentElement;
      return {{text:c.innerText.replace(/\\s+/g,' ').slice(0,80),buttons:[...c.querySelectorAll('button')].filter(b=>b.offsetParent)
        .map(b=>{{const r=b.getBoundingClientRect();return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)]}})}}}})()""")


def ensure_serve():
    """TP 瀏覽器沒開就自己在背景開，這支程式結束時自己關（用完即關）；已經開著的不動、也不關
    （可能是使用者或別的流程開的）。環境變數會傳給 serve；TP_HEADLESS=1 不要用（無頭開 TP 多半落在登入頁）。"""
    import atexit, socket

    def up():
        with socket.socket() as so:
            so.settimeout(0.5)
            return so.connect_ex(("127.0.0.1", 9333)) == 0

    if up():
        return None
    log = open(serve_log(os.environ, Path.home()), "w")
    proc = subprocess.Popen([sys.executable, HERE / "tp_browser.py", "serve"], stdout=log, stderr=subprocess.STDOUT)

    def stop():
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()

    atexit.register(stop)
    for _ in range(60):
        if up():
            time.sleep(8)                          # 等首頁載完再開始操作
            print("TP browser: started here, will close when done" + (" (headless)" if os.environ.get("TP_HEADLESS") == "1" else ""))
            return proc
        if proc.poll() is not None:
            break
        time.sleep(1)
    sys.exit(f"✗ the TP browser did not start; see {log.name}")


def close_modal():
    """上一次失敗的流程會留著「Create a Video」視窗，擋住下一段的建立流程。"""
    if ev("[...document.querySelectorAll('*')].some(e=>e.children.length===0&&e.textContent.trim()==='Close modal')"):
        tp("click", "Close modal")


def busy(c):
    return c and any(w in c["text"].lower() for w in ("pending", "processing"))


def upload(label, mp3, tmp):
    go("#/media-library")
    tp("click", AUDIO_DIR)                  # 點座標打不開資料夾
    time.sleep(4)
    if has(label):
        return "already in the media library"
    f = tmp / f"{label}.mp3"
    f.write_bytes(mp3.read_bytes())
    # 「Upload File」是開關：上傳面板可能已經開著，按一下反而關掉，檔案就沒傳上去
    for _ in range(2):
        if ev("document.querySelectorAll('input[type=file]').length"):
            break
        tp("click", "Upload File")
        time.sleep(2)
    if "uploaded" not in tp("upload", "input[type=file]", f, timeout=180):
        sys.exit(f"✗ {label}: no upload field (input[type=file]); nothing uploaded")
    for _ in range(15):
        time.sleep(4)
        if has(label):
            return "uploaded"
    sys.exit(f"✗ {label}: the audio file did not appear in the media library after uploading")


def fail_shot(label, shot_dir):
    """送出失敗時存一張 TP 頁面的截圖，回傳要接在錯誤訊息後面的那一行（沒給資料夾或存不成回空字串）。"""
    if not shot_dir:
        return ""
    png = Path(shot_dir) / f"fail_{label.replace(' ', '_')}.png"
    try:
        tp("shot", png)
    except Exception:   # 截圖只是幫忙看原因，存不成不能蓋掉原本的錯誤
        return ""
    return f"\npage screenshot: {png}" if png.exists() else ""


def submit(label, dry=False, look=None, shot_dir=None):
    # 每段都從頭開新流程：接著上一次的流程換音檔（tp_swap）會沿用上一次的角色，要用原版角色的那一集會做成上一集的造型
    script, args = "tp_submit.sh", [label, label] + ([look] if look else [])
    out = subprocess.run([HERE / script, *args], capture_output=True, text=True, timeout=300).stdout
    names = ev("[...document.querySelectorAll('input')].filter(e=>e.offsetParent).map(e=>e.value)") or []
    # 選中的音檔名只在「選音檔」那一步看得到，到 Render 頁就不顯示：從腳本輸出確認（tp_swap／tp_submit 會印出選中的卡片）
    picked = f'"{label} (mp3)"' in out
    if label not in names or not picked:
        sys.exit(f"✗ {label}: after {script} the name fields are {names}, audio picked {picked}; not rendering\n{out[-600:]}{fail_shot(label, shot_dir)}")
    if dry:
        return f"filled in with {script}; dry run stopped before Render"
    n = ev("(()=>{const b=[...document.querySelectorAll('button')].filter(e=>e.offsetParent&&e.innerText.trim()==='Render Video');"
           "b[b.length-1].click();return b.length})()")
    # 新造型第一次用時「Being Rendered」可能超過 6 秒才出現，最多等 30 秒
    for _ in range(15):
        time.sleep(2)
        if leaf_texts("Being Rendered"):
            break
    else:
        sys.exit(f"✗ {label}: clicked Render Video ({n} button(s)) but saw no \"Being Rendered\" within 30 seconds")
    return f"filled in with {script} and sent to render"


def duration(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True, check=True).stdout)


def streams(f):
    return set(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", f],
                              capture_output=True, text=True).stdout.split())


def main():
    ap = argparse.ArgumentParser(description="Host segments in one go: upload the audio -> send it to TP to render -> wait -> "
                                             "download -> check the length. Rerunnable: skips what is already uploaded or sent.")
    ap.add_argument("project"); ap.add_argument("--prefix", required=True, help="TP name prefix, e.g. Ep01r2")
    ap.add_argument("--parts", type=int, nargs="*", help="only these segments (default: all of parts.json)")
    ap.add_argument("--timeout", type=float, default=30, help="max minutes to wait for each segment after sending it (proposed value; the first run took 23 minutes)")
    ap.add_argument("--tol", type=float, default=TOL_DEFAULT, help="allowed difference between the download and the audio length (seconds)")
    ap.add_argument("--dry-run", action="store_true", help="upload and fill in the create flow, stop before clicking Render (spends no render)")
    ap.add_argument("--look", help="host look = image name in TP Media Library Images (e.g. Host shirt; upload it with tp_upimg.py before first use); omit to use the original character")
    ap.add_argument("--skip-checklist", help="run even if the opening checklist (tools/checklist) fails: give the reason; it is logged in <episode>/nightly/checklist_skips.jsonl")
    a = ap.parse_args()
    P = Path(a.project).resolve()
    checklist.gate(P, "start", a.skip_checklist, "tp")   # 送 TP 花渲染：開工清單不過就停
    parts = a.parts or [p["k"] for p in json.loads((P / "host/parts.json").read_text())]
    tmp = P / "host/tp_upload"
    tmp.mkdir(exist_ok=True)
    ensure_serve()
    url = (tp("shot", tmp / "start.png").splitlines() or [""])[0]
    if "talkingphotos" not in url:
        sys.exit(f"✗ cannot reach the TP browser ({url or 'no response'}): run python3 tools/tp/tp_browser.py serve in the background first")
    if "login" in url.lower() or leaf_texts("^(Log ?in|Sign ?in)$"):
        sys.exit(TP_LOGIN)
    prefix = tp_name(a.prefix)
    labels = {k: f"{prefix} part{k}" for k in parts}

    for k in labels:
        if not (P / f"host/parts/part{k}.mp3").exists():
            sys.exit(f"✗ no {P / f'host/parts/part{k}.mp3'}: run doc_host.py split first")

    def send(k):
        label = labels[k]
        close_modal()
        print(f"{label}: {upload(label, P / f'host/parts/part{k}.mp3', tmp)}; create flow {submit(label, a.dry_run, a.look, tmp)}")
        go("#/my-videos", 5)
        if not a.dry_run and not card(label):
            sys.exit(f"✗ {label}: no card in My Videos after sending")

    go("#/my-videos", 5)
    queue, sent = [], {}                            # sent：段號 → 開始等的時間
    for k, label in labels.items():
        if card(label):
            print(f"{label}: already in My Videos, not sending again")
            sent[k] = time.time()
        else:
            queue.append(k)
    if a.dry_run:
        for k in queue:
            send(k)
        return print("dry run done, nothing sent to render")
    # 超過上限的段落排隊：前面的完成一段才送下一段（上限見 MAX_ACTIVE）
    while queue and len(sent) < MAX_ACTIVE:
        k = queue.pop(0)
        send(k)
        sent[k] = time.time()
    if queue:
        print(f"at most {MAX_ACTIVE} renders at once: part{', part'.join(map(str, queue))} queued, each sent when an earlier one finishes")
    t0, left = time.time(), dict(labels)
    while left:
        ev("(()=>{location.reload();return 1})()")
        time.sleep(8)
        for k in [k for k in sent if k in left]:
            label = labels[k]
            c = card(label)
            if c is None:
                sys.exit(f"✗ {label}: card not found in My Videos")
            if busy(c):
                continue
            if any(w in c["text"].lower() for w in ("fail", "error")):
                sys.exit(f"✗ {label}: TP render failed ({c['text']})")
            out = P / f"host/parts/part{k}.mp4"
            if out.exists():
                out.rename(out.with_suffix(".bak.mp4"))
            if len(c["buttons"]) < 2:
                sys.exit(f"✗ {label}: card has fewer than 2 buttons {c}")
            for _ in range(3):                      # 剛 reload 版面還在動，第一下常點空
                x, y = c["buttons"][1]              # 第 2 顆＝下載
                tp("download", x, y, out, timeout=300)
                if out.exists():
                    break
                time.sleep(5)
                c = card(label) or c
            if not out.exists():
                sys.exit(f"✗ {label}: clicked download but no {out.name} appeared")
            mp3 = P / f"host/parts/part{k}.mp3"
            d = abs(duration(out) - duration(mp3))
            if d > a.tol or not {"video", "audio"} <= streams(out):
                sys.exit(f"✗ {label}: download length off by {d:.2f}s (allowed {a.tol}) or missing video/audio {streams(out)}")
            print(f"{label}: done, downloaded {out.name}, length off by {d:.2f}s, waited {(time.time() - t0) / 60:.0f} min")
            del left[k]
        while queue and sum(k in left for k in sent) < MAX_ACTIVE:
            k = queue.pop(0)
            send(k)
            sent[k] = time.time()
        late = [labels[k] for k in sent if k in left and time.time() - sent[k] > a.timeout * 60]
        if late:
            print(f"✗ not ready after more than {a.timeout} minutes: {', '.join(late)}")
            sys.exit(2)
        if left:
            time.sleep(52)
    print("all done")


if __name__ == "__main__":
    main()
