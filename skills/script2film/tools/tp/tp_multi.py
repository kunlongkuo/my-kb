"""跨集送主持人分段：好幾集的段排成一條隊伍，TP 空出名額就補下一段，讓同時渲染一直滿 5 段。

  python3 tools/tp/tp_multi.py <集資料夾>:<prefix>[:<look>] <集資料夾>:<prefix>[:<look>] ... [--timeout 30]

例：tp_multi.py projects/<系列>/001_示範:E01:Host\\ shirt projects/<系列>/002_示範:E02:Host\\ bible
不給 look 用原版角色（同 tp_host --look）。每集先跑 doc_host.py split；之後各集照常 doc_host.py join。
上傳、送出、找卡、下載都用 tp_host 的函式，行為跟 tp_host 一樣（可重跑：已有的段不再送，只等與下載）。
和 tp_host 不同的地方：
- 隊伍依集的順序排（第一集的段先送），完成一段就補一段，不等整集。
- 一段出錯（找不到卡片、渲染失敗、長度不對）只記下那一段、其他段繼續；最後列出失敗的段，退出碼 1。
  找不到卡片先重試 3 輪再算失敗（遇過首輪找不到、重跑就有）。
- 送出失敗的段排到隊尾再送一次；每輪查卡前先回 My Videos 再 reload。
- 全部集共用 MAX_ACTIVE（帳號同時渲染上限 5）。
退出碼 0＝全部下載且驗過；1＝有段失敗；2＝有段等超過 --timeout 分鐘。
"""
import argparse, json, sys, time
from pathlib import Path

from tp_host import MAX_ACTIVE, TOL_DEFAULT, busy, card, close_modal, duration, ensure_serve, ev, go, leaf_texts, TP_LOGIN, streams, submit, tp, upload

sys.stdout.reconfigure(line_buffering=True)   # nohup 寫 log 時逐行出現（不設的話整批跑完前 log 都是空的）

MISS_RETRY = 3
SUBMIT_RETRY = 2   # 一段最多送 2 次


def parse_job(spec):
    """'<集資料夾>:<prefix>[:<look>]' → (Path, prefix 首字大寫, look 或 None)。prefix 不能空。"""
    parts = spec.split(":", 2)
    if len(parts) < 2 or not parts[1]:
        raise ValueError(f"expected <episode folder>:<prefix>[:<look>]: {spec}")
    look = parts[2] if len(parts) == 3 and parts[2] else None
    return Path(parts[0]).resolve(), parts[1][:1].upper() + parts[1][1:], look


def build_queue(jobs):
    """每集 host/parts.json 的段 → [(集序, 段號, label, mp3, mp4, look)]，依集的順序、段號排。"""
    q = []
    for i, (P, prefix, look) in enumerate(jobs):
        for p in json.loads((P / "host/parts.json").read_text()):
            k = p["k"]
            q.append((i, k, f"{prefix} part{k}", P / f"host/parts/part{k}.mp3", P / f"host/parts/part{k}.mp4", look))
    return q


def done_ok(it, tol):
    """重跑時：這段已經下載、長度跟音檔差在容許內、有畫面與聲音，就不再等（中斷後接續）。"""
    out, mp3 = it[4], it[3]
    return out.exists() and abs(duration(out) - duration(mp3)) <= tol and {"video", "audio"} <= streams(out)


def main():
    ap = argparse.ArgumentParser(description="Send host segments across episodes: one queue, the next segment goes out as soon as "
                                             "TP has a free slot, so 5 renders keep running. Rerunnable like tp_host.py.")
    ap.add_argument("jobs", nargs="+", help="<episode folder>:<prefix>[:<look>]")
    ap.add_argument("--timeout", type=float, default=30)
    ap.add_argument("--tol", type=float, default=TOL_DEFAULT)
    a = ap.parse_args()
    jobs = [parse_job(s) for s in a.jobs]
    queue = build_queue(jobs)
    for it in queue:
        if not it[3].exists():
            sys.exit(f"✗ no {it[3]}: run doc_host.py split first")
    tmp = jobs[0][0] / "host/tp_upload"
    tmp.mkdir(exist_ok=True)
    ensure_serve()
    url = (tp("shot", tmp / "start.png").splitlines() or [""])[0]
    if "talkingphotos" not in url:
        sys.exit(f"✗ cannot reach the TP browser ({url or 'no response'}): run python3 tools/tp/tp_browser.py serve in the background first")
    if "login" in url.lower() or leaf_texts("^(Log ?in|Sign ?in)$"):
        sys.exit(TP_LOGIN)

    go("#/my-videos", 5)
    sent, waiting, failed, miss, tries = {}, [], {}, {}, {}     # sent：label → (item, 開始等的時間)；tries：送出失敗次數
    for it in queue:
        if done_ok(it, a.tol):
            print(f"{it[2]}: already downloaded with the right length, skipped")
            continue
        if card(it[2]):
            print(f"{it[2]}: already in My Videos, not sending again")
            sent[it[2]] = (it, time.time())
        else:
            waiting.append(it)

    def send(it):
        label = it[2]
        close_modal()
        try:
            msg = f"{upload(label, it[3], jobs[it[0]][0] / 'host/tp_upload')}; create flow {submit(label, False, it[5], jobs[it[0]][0] / 'host/tp_upload')}"
        except SystemExit as e:                       # tp_host 的函式失敗時 sys.exit：只記這一段
            close_modal()
            go("#/my-videos", 5)
            tries[label] = tries.get(label, 0) + 1
            if tries[label] < SUBMIT_RETRY:           # 送出失敗多半是剛上傳的音檔還搜不到，排到隊尾晚點再送（遇過重跑就過）
                print(f"✗ {label}: send failed, moved to the end of the queue to try once more ({str(e).splitlines()[0]})")
                waiting.append(it)
                return
            failed[label] = str(e)
            print(f"✗ {label}: send failed, skipped ({e})")
            return
        print(f"{label}: {msg}")
        go("#/my-videos", 5)
        sent[label] = (it, time.time())

    def fill():
        for _ in range(len(waiting)):                 # 每段每輪只試一次：送出失敗排回隊尾的段等下一輪（約 1 分鐘）再送
            if len(sent) >= MAX_ACTIVE:
                break
            send(waiting.pop(0))

    for P, _, _ in jobs:
        (P / "host/tp_upload").mkdir(exist_ok=True)
    fill()
    t0 = time.time()
    while sent or waiting:
        # 先把網址改回 My Videos 再 reload：送出失敗時頁面會停在建立流程，單純 reload 還是建立流程頁，
        # 每段都找不到卡片（遇過一段送出失敗後，正在渲染的 3 段連 3 輪「找不到」）
        ev("(()=>{location.hash='#/my-videos';location.reload();return 1})()")
        time.sleep(8)
        for label, (it, ts) in list(sent.items()):
            c = card(label)
            if c is None:
                miss[label] = miss.get(label, 0) + 1
                if miss[label] >= MISS_RETRY:
                    failed[label] = f"card not found in My Videos for {MISS_RETRY} rounds"
                    print(f"✗ {label}: {failed[label]}, skipped")
                    del sent[label]
                continue
            miss.pop(label, None)
            if busy(c):
                continue
            if any(w in c["text"].lower() for w in ("fail", "error")):
                failed[label] = f"TP render failed ({c['text']})"
                print(f"✗ {label}: {failed[label]}")
                del sent[label]
                continue
            out, mp3 = it[4], it[3]
            if out.exists():
                out.rename(out.with_suffix(".bak.mp4"))
            for _ in range(3):                        # 剛 reload 版面還在動，第一下常點空（同 tp_host）
                if len(c["buttons"]) >= 2:
                    x, y = c["buttons"][1]
                    tp("download", x, y, out, timeout=300)
                if out.exists():
                    break
                time.sleep(5)
                c = card(label) or c
            del sent[label]
            if not out.exists():
                failed[label] = f"clicked download but no {out.name} appeared"
                print(f"✗ {label}: {failed[label]}")
                continue
            d = abs(duration(out) - duration(mp3))
            if d > a.tol or not {"video", "audio"} <= streams(out):
                failed[label] = f"length off by {d:.2f}s (allowed {a.tol}) or missing video/audio {streams(out)}"
                print(f"✗ {label}: {failed[label]}")
                continue
            print(f"{label}: done, downloaded {out.parent.parent.parent.name}/{out.name}, length off by {d:.2f}s, at minute {(time.time() - t0) / 60:.0f}")
        fill()
        late = [label for label, (_, ts) in sent.items() if time.time() - ts > a.timeout * 60]
        if late:
            print(f"✗ not ready after more than {a.timeout} minutes: {', '.join(late)} (rerun the same command to keep waiting)")
            sys.exit(2)
        if sent or waiting:
            time.sleep(52)
    if failed:
        print("✗ failed segments: " + "; ".join(f"{k}: {v}" for k, v in failed.items()) + " (rerun the same command to redo them)")
        sys.exit(1)
    print(f"all done, {len(queue)} segments, {(time.time() - t0) / 60:.0f} min")


if __name__ == "__main__":
    main()
