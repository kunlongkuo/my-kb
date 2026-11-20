"""Keep a headed Chrome open on the logged-in TalkingPhotos profile with a CDP port, so each step can connect, act and leave.

serve: python3 tp_browser.py serve            (blocks; run in background)
shot:  python3 tp_browser.py shot <out.png>    (screenshot of the TP tab + prints url and visible buttons)
click: python3 tp_browser.py click "<text>"    (click the first visible element whose text matches exactly)
eval:  python3 tp_browser.py eval "<js>"       (prints the result)
upload:python3 tp_browser.py upload "<css>" <file>
fill:  python3 tp_browser.py fill "<css>" "<text>"  (type into the last matching input, press Enter)
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import os, sys, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tp_paths import idle_expired, idle_minutes, last_use_file, profile_dir  # noqa: E402

# TP 專用設定檔：和 VE 的分開，兩邊可以同時跑，不搶同一個 profile。
# 放在 repo 外（含登入 cookie，不能進版控）；TP 登入過期時在這個 profile 重新登入，VE 那份不受影響。
# 位置：S2F_TP_PROFILE → 舊名 TP_PROFILE → ~/.config/script2film/tp-profile（舊版的預設資料夾已存在而新位置沒有時沿用舊的；tp_paths.py）。
PROFILE = profile_dir(os.environ, Path.home())
PORT = 9333
LAST_USE = last_use_file(os.environ, Path.home())   # 每個單步指令摸一下；serve 靠它知道還有沒有人在用


def touch():
    try:
        LAST_USE.parent.mkdir(parents=True, exist_ok=True)
        LAST_USE.touch()
    except OSError:
        pass
URL = "https://app.talkingphotos.ai/#/homepage"


def tp_page(browser):
    for ctx in browser.contexts:
        for p in ctx.pages:
            if "talkingphotos" in p.url:
                return p
    return browser.contexts[0].pages[0]


cmd = sys.argv[1]
with sync_playwright() as pw:
    if cmd == "serve":
        # TP_HEADLESS=1：不開視窗。試驗的結論是不要用（無頭開 TP 多半落在登入頁），
        # 開關只留作紀錄；預設開視窗。無頭沒有真視窗，要給固定頁面大小。
        opts = dict(headless=True, viewport={"width": 1600, "height": 1100}) if os.environ.get("TP_HEADLESS") == "1" \
            else dict(headless=False, no_viewport=True)
        # chromium_sandbox=True：不讓 Playwright 加 --no-sandbox（視窗上方會多一條警告，也少一層保護；ve_runner 同樣設定）
        ctx = pw.chromium.launch_persistent_context(str(PROFILE), channel="chrome", chromium_sandbox=True, **opts,
                                                    args=["--window-size=1600,1100", f"--remote-debugging-port={PORT}"],
                                                    ignore_default_args=["--enable-automation"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL)
        touch()
        idle = idle_minutes(os.environ)
        print("ready" + (f" (closes itself after {idle:g} minutes without a command)" if idle else ""), flush=True)
        # 被 kill（SIGTERM）時也要好好關瀏覽器，讓登入狀態寫回設定檔：連續直接砍掉三次 serve 之後 TP 變成登入頁
        # （推測是剛換發的登入憑證還沒寫進磁碟就被砍掉；沒有直接證據）。
        import signal
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
        try:
            while ctx.pages:
                time.sleep(2)
                # 閒置自動關：沒有任何單步指令連進來超過 idle 分鐘（等渲染時 tp_host 每分鐘會來查一次，不會被關）。
                # 走和 SIGTERM 一樣的正常收尾，登入狀態會寫回設定檔。
                try:
                    last = LAST_USE.stat().st_mtime
                except OSError:
                    touch()
                    continue
                if idle_expired(time.time(), last, idle):
                    print(f"idle: no command for {idle:g} minutes, closing", flush=True)
                    break
        finally:
            try:
                ctx.close()
            except Exception:
                pass
        sys.exit(0)
    touch()
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
    page = tp_page(browser)
    if cmd == "shot":
        page.screenshot(path=sys.argv[2])
        print(page.url)
        print(json.dumps(page.evaluate("""() => [...document.querySelectorAll('button,a,[role=button],input,textarea,label')]
            .filter(e => e.offsetParent).map(e => (e.tagName + ':' + (e.innerText || e.value || e.placeholder || e.type || '').trim().slice(0, 40)))
            .filter(s => s.length > 2).slice(0, 80)"""), ensure_ascii=False))
    elif cmd == "fill":     # type into the last visible input matching css and press Enter (React search boxes need real typing)
        el = page.locator(sys.argv[2]).last
        el.fill(sys.argv[3])
        el.press("Enter")
        time.sleep(3)
        print("filled", sys.argv[3])
    elif cmd == "click":
        page.get_by_text(sys.argv[2], exact=True).first.click()
        time.sleep(1.5)
        print("clicked", page.url)
    elif cmd == "clickxy":   # CSS px (screenshot px / 2 on this Retina window)
        page.mouse.click(float(sys.argv[2]), float(sys.argv[3]))
        time.sleep(1.5)
        print("clicked at", sys.argv[2], sys.argv[3])
    elif cmd == "chooser":   # click a button that opens the OS file picker and answer it with a file
        with page.expect_file_chooser() as fc:
            page.get_by_text(sys.argv[2], exact=True).first.click()
        fc.value.set_files(sys.argv[3])
        time.sleep(3)
        print("chose", sys.argv[3])
    elif cmd == "eval":
        print(json.dumps(page.evaluate(sys.argv[2]), ensure_ascii=False)[:4000])
    elif cmd == "upload":
        page.set_input_files(sys.argv[2], sys.argv[3])
        print("uploaded")
    elif cmd == "fill":      # fill "<css>" "<text>" (types like a user so the page's input handlers fire)
        page.locator(sys.argv[2]).first.fill(sys.argv[3])
        print("filled")
    elif cmd == "download":  # download x y <out>: click at CSS px and save the download it starts
        with page.expect_download(timeout=120000) as dl:
            page.mouse.click(float(sys.argv[2]), float(sys.argv[3]))
        dl.value.save_as(sys.argv[4])
        print("saved", sys.argv[4], dl.value.url[:120])
    touch()   # 做完再摸一次：下載這類長指令做完才開始算閒置
