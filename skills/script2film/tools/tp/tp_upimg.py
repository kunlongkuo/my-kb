"""把造型圖上傳到 TP Media Library > Images（tp_submit 用名字找圖）。TP 檔案只留 60 天，tp_multi／tp_host 報「✗ no look "…" in Media Library Images」就用這支補傳。
用法：python3 tools/tp/tp_upimg.py [--fit | --as-is] "<造型名>.jpg" ...（先背景跑 tp_browser.py serve；它 10 分鐘沒有指令會自己關）

上傳前量圖的寬高：比例和 TP_ASPECT（預設 16:9）不合就停，不碰瀏覽器。造型圖要先照取景規則做好（docs/FLOW.md 選用 B）；
--fit：比例不合的圖置中裁成 TP_ASPECT 再傳（裁在暫存副本上，原檔不動；生圖工具常出 1376×768 這種接近但不等於 16:9 的尺寸）。
--as-is：不裁、照傳（TP 會跳出裁切確認）。兩個不能同時給。
TP 顯示的名字不一定等於檔名（實測：檔名的底線顯示成空白、開頭變大寫）：比對時把 _ 與 - 當空白、不分大小寫，成功時印出 TP 顯示的
名字，tp_host.py --look 要填那個名字。"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / 'tools/config'))
import s2f_config; s2f_config.load()
import json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path
TB = Path(__file__).resolve().parent / "tp_browser.py"
USAGE = """Upload look images to TP Media Library > Images (tp_submit finds them by name). TP keeps files only 60 days:
when tp_multi/tp_host report "✗ no look "…" in Media Library Images", re-upload with this.
usage: python3 tools/tp/tp_upimg.py [--fit | --as-is] "<look name>.jpg" ...
  (run tp_browser.py serve in the background first; it closes itself after 10 minutes without a command)

Stops before touching the browser when an image's aspect ratio is not TP_ASPECT (default 16:9).
--fit: center-crop such images to TP_ASPECT and upload the crop (a temporary copy; the original is untouched;
  image tools often output sizes like 1376×768 that are close to but not exactly 16:9).
--as-is: upload without cropping (TP will ask about cropping). Give at most one of the two.
Look images must follow the framing rules first (docs/FLOW.md optional B).
The name TP shows is not always the file name (measured: underscores show as spaces, the first letter is capitalized):
matching treats _ and - as spaces and ignores case; on success it prints the name TP shows, and tp_host.py --look
takes that name."""


def tp(*a, timeout=200):
    return subprocess.run([sys.executable, str(TB), *map(str, a)], capture_output=True, text=True, timeout=timeout).stdout.strip()


def norm(s):
    """名字比對用：_ 與 - 當空白、連續空白併成一個、不分大小寫。"""
    return re.sub(r"[\s_-]+", " ", s).strip().lower()


def aspect_ok(w, h, aspect):
    """寬高合不合 "16:9" 這種比例：照寬度換算出來的高，和實際的高差不到 1 像素（整數取整的誤差）。"""
    a, b = (int(x) for x in aspect.split(":"))
    return abs(w * b / a - h) < 1


def fit_box(w, h, aspect):
    """置中裁成 aspect 的框 (寬, 高, x, y)：比例剛好、寬高都是偶數（JPEG 存檔會把奇數邊長改成偶數）的最大一塊。"""
    a, b = (int(x) for x in aspect.split(":"))
    k = min(w // a, h // b)
    k -= k % 2
    cw, ch = a * k, b * k
    return cw, ch, (w - cw) // 2, (h - ch) // 2


def fit_copy(path, size, aspect, out_dir):
    """把 path 置中裁成 aspect 存到 out_dir（同檔名：TP 用檔名當造型名）；回 (新路徑, 裁切框)。ffmpeg 失敗就停。"""
    box = fit_box(*size, aspect)
    if box[0] <= 0:
        sys.exit(f"✗ {path.name} is too small to crop to {aspect}")
    out = Path(out_dir) / path.name
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", "crop=%d:%d:%d:%d" % box, "-q:v", "2", str(out)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        sys.exit(f"✗ {path.name}: crop failed: {r.stderr.strip()}")
    return out, box


def image_size(path):
    """(寬, 高)；ffprobe 讀不出來（或讀到 0×0）回 None。"""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json",
                        str(path)], capture_output=True, text=True)
    try:
        s = json.loads(r.stdout)["streams"][0]
        w, h = int(s["width"]), int(s["height"])
    except (ValueError, KeyError, IndexError):
        return None
    return (w, h) if w > 0 and h > 0 else None   # 不是圖檔時 ffprobe 也會回 0×0


def aspect_problem(path, aspect):
    """比例不合時的一行說明；合就回 None。"""
    size = image_size(path)
    if size is None:
        return f"✗ {path.name}: cannot read width and height (not an image?)"
    w, h = size
    if aspect_ok(w, h, aspect):
        return None
    cw, ch, _, _ = fit_box(w, h, aspect)
    return (f"✗ {path.name} is {w}×{h}, TP_ASPECT is {aspect}. Add --fit to center-crop it to {cw}×{ch}"
            f" (cuts {w - cw} px left and right in total, {h - ch} px top and bottom in total; the original is untouched);"
            f" if it is far off, remake the look image by the framing rules (docs/FLOW.md optional B); --as-is uploads it unchanged")


def shown_name(stem):
    """媒體庫頁面上和這個檔名對得上的那個名字（TP 顯示的原文字）；沒有回 ""。"""
    js = ("(()=>{const n=s=>s.replace(/[\\s_-]+/g,' ').trim().toLowerCase();"
          "const e=[...document.querySelectorAll('*')].find(e=>e.children.length===0&&n(e.textContent)===%s);"
          "return e?e.textContent.trim():''})()" % json.dumps(norm(stem)))
    return tp("eval", js).strip('"')


TP_LOGIN = ("✗ TP is on the login page: ask the user to log in themselves in the open TP window (never type the password for them), "
            "then rerun this command. The window closes itself after 10 minutes without a command (S2F_TP_IDLE_MIN); "
            "if it closed, run python3 tools/tp/tp_browser.py serve in the background again")
PAGE_STATE = ("(()=>{const t=[...document.querySelectorAll('*')].some(e=>e.offsetParent&&e.children.length===0&&"
              "/^(Log ?in|Sign ?in)$/.test(e.textContent.trim()));return (/login/i.test(location.href)||t)?'login':'ok'})()")


def page_problem(state):
    """tp eval PAGE_STATE 的回答 → 要停下時的訊息；可以往下做回 None。沒有回答＝serve 沒在跑。"""
    if not state:
        return "✗ cannot reach the TP browser: run python3 tools/tp/tp_browser.py serve in the background first"
    return TP_LOGIN if "login" in state else None


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    as_is, fit = "--as-is" in args, "--fit" in args
    files = [Path(x) for x in args if x not in ("--as-is", "--fit")]
    if not files:
        sys.exit(USAGE)
    if as_is and fit:
        sys.exit("✗ give only one of --fit and --as-is")
    aspect = os.environ.get("TP_ASPECT") or "16:9"
    tmp = None
    if not as_is:
        bad = [(f, p) for f in files if (p := aspect_problem(f, aspect))]
        unreadable = [p for f, p in bad if image_size(f) is None]
        if unreadable or (bad and not fit):
            sys.exit("\n".join(unreadable or [p for _, p in bad]))
        if bad:
            tmp = tempfile.mkdtemp(prefix="tp_upimg_")
            for f, _ in bad:
                size = image_size(f)
                out, box = fit_copy(f, size, aspect, tmp)
                print(f"{f.name}: {size[0]}×{size[1]} center-cropped to {box[0]}×{box[1]} (original untouched)")
                files[files.index(f)] = out
    try:
        if stop := page_problem(tp("eval", PAGE_STATE)):   # 第一次用的機器會落在登入頁：不要等 60 秒才說「沒看到」
            sys.exit(stop)
        upload(files)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def upload(files):
    for f in files:
        tp("eval", "(()=>{location.hash='#/media-library';return 1})()"); time.sleep(5)
        tp("click", "Images"); time.sleep(5)
        if name := shown_name(f.stem):
            print(f"{f.stem} is already in the media library; TP shows it as \"{name}\" (use this for --look)"); continue
        for _ in range(2):
            if tp("eval", "document.querySelectorAll('input[type=file]').length") not in ("0", ""):
                break
            tp("click", "Upload File"); time.sleep(2)
        print(f.stem, tp("upload", "input[type=file]", f))
        for _ in range(20):
            time.sleep(3)
            if name := shown_name(f.stem):
                print(f"{f.stem} ✓ appears in Images; TP shows it as \"{name}\" (use this for --look)"); break
        else:
            print(f.stem, "✗ not seen")


if __name__ == "__main__":
    main()
