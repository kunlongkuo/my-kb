"""YouTube 上稿（Data API v3）。

  tools/youtube/.venv/bin/python tools/youtube/yt_upload.py auth      # 第一次：開瀏覽器授權，存 refresh token
  tools/youtube/.venv/bin/python tools/youtube/yt_upload.py whoami    # 驗證授權：印出頻道名稱
  tools/youtube/.venv/bin/python tools/youtube/yt_upload.py upload <影片.mp4> --title ... --desc-file ... [--thumb 圖.png] [--playlist ID] [--publish-at 2026-10-25T08:00:00+08:00]
  tools/youtube/.venv/bin/python tools/youtube/yt_upload.py thumb <影片 ID> <圖.jpg>   # 已上傳的片換縮圖
  tools/youtube/.venv/bin/python tools/youtube/yt_upload.py private <影片 ID>   # 改成私人並取消排定公開（重傳替換版時把舊的撤下）
  tools/youtube/.venv/bin/python tools/youtube/yt_upload.py plswap <舊 ID> <新 ID> <清單 ID,...>   # 換片：新的移到舊的在清單裡的位置，舊的移出清單（影片不刪）

憑證放家目錄、不進專案：~/.config/script2film/youtube/youtube_client_secret.json（OAuth 電腦版用戶端）、同資料夾 youtube_token.json（授權後產生）。
資料夾可用 S2F_YT_DIR 指定（yt_paths.py）。
另一個頻道：命令前加 YT_ACCOUNT=second（權杖存在同一個資料夾的 youtube_token_second.json；auth 時在 Google 的選頻道畫面選那個頻道）。
預設上傳「不公開」（unlisted）；加 --publish-at <ISO 時間> 改成私人＋排定該時刻自動公開（時間可由 tools/nightly/yt_meta.py 依集數算好）。
時間已過或 15 分鐘內就停下不傳（斷檔要讓人看見，不自動往後延）。API 專案未通過審核前，上傳的片會被 YouTube 鎖成私人且改不回
（support.google.com/youtube/answer/7300965），這時改用瀏覽器上傳。
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import argparse, json, os, sys, time
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yt_paths import creds_dir  # noqa: E402
from yt_snippet import upload_snippet  # noqa: E402

HOME = creds_dir(os.environ, Path.home())
# 第二個頻道：YT_ACCOUNT=<名稱> 用另一份權杖 youtube_token_<名稱>.json，不動預設頻道的權杖
_acct = os.environ.get("YT_ACCOUNT", "").strip()
SECRET = HOME / "youtube_client_secret.json"
TOKEN = HOME / (f"youtube_token_{_acct}.json" if _acct else "youtube_token.json")
# youtube（管理）才能加播放清單；token 缺這個範圍時 creds() 會要求重跑 auth
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]


def creds(interactive=False):
    # 不傳 SCOPES：傳了會把檔內範圍蓋成 SCOPES，下面的比對永遠通過（加了範圍卻沒重新授權時就驗不出來）
    c = Credentials.from_authorized_user_file(str(TOKEN)) if TOKEN.exists() else None
    if c and not set(SCOPES) <= set(c.scopes or []):
        c = None
    if c and c.expired and c.refresh_token:
        try:
            c.refresh(Request())
        except RefreshError:   # refresh token 過期或被撤銷：當成未授權，auth 會重新走授權頁
            c = None
    if not (c and c.valid):
        if not interactive:
            sys.exit("✗ not authorized, or the authorization expired: run yt_upload.py auth first")
        c = InstalledAppFlow.from_client_secrets_file(str(SECRET), SCOPES).run_local_server(port=0, prompt="consent")
    TOKEN.write_text(c.to_json())
    TOKEN.chmod(0o600)
    return c


def set_thumb(yt, vid, image):
    """Custom thumbnail (doc_thumb.py). Returns None, or the error text: a failed thumbnail never fails the upload,
    because the video is already in and retrying the upload would make a second copy."""
    try:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(image)).execute()
        return None
    except Exception as e:   # e.g. channel not verified for custom thumbnails
        print(f"✗ thumbnail not set (the video is uploaded): {e}", file=sys.stderr)
        return str(e)[:200]


def main():
    ap = argparse.ArgumentParser(description="Upload to YouTube (Data API v3): auth, whoami, scopes, upload, thumb, show, desc, "
                                             "private, plswap. Credentials live in ~/.config/script2film/youtube/ (S2F_YT_DIR); "
                                             "YT_ACCOUNT=<name> uses a second channel's token.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth"); sub.add_parser("whoami"); sub.add_parser("scopes")
    pv = sub.add_parser("private"); pv.add_argument("video_id")
    ps = sub.add_parser("plswap"); ps.add_argument("old_id"); ps.add_argument("new_id"); ps.add_argument("playlists")
    th = sub.add_parser("thumb"); th.add_argument("video_id"); th.add_argument("image")
    sh = sub.add_parser("show"); sh.add_argument("video_id")                                   # 標題、標籤、狀態（換片前先看舊片）
    de = sub.add_parser("desc"); de.add_argument("video_id"); de.add_argument("desc_file")     # 只換說明欄（上下集互相連結）
    up = sub.add_parser("upload")
    up.add_argument("video"); up.add_argument("--title", required=True); up.add_argument("--desc-file", required=True)
    up.add_argument("--tags", default=""); up.add_argument("--thumb", default="")
    up.add_argument("--playlist", default="", help="playlist IDs, comma-separated (e.g. the main and part playlists printed by series.py <episode> playlists)")
    up.add_argument("--privacy", default="unlisted", choices=["unlisted", "private"])
    up.add_argument("--publish-at", default="", help="ISO time with a time zone, e.g. 2026-10-25T08:00:00+08:00: private + scheduled to go public")
    up.add_argument("--category", default="27", help="category ID: 27 Education (default), 25 News & Politics")
    up.add_argument("--language", default="zh-Hant", help="the video's default language, e.g. zh-Hant, en")
    up.add_argument("--synthetic", action="store_true", help="tick \"Altered or synthetic content\" (containsSyntheticMedia; the API writes it but does not read it back)")
    up.add_argument("--skip-checklist", help="run even if the opening checklist (tools/checklist) fails (or the video is not in an episode folder): give the reason; it is logged in <episode>/nightly/checklist_skips.jsonl (next to the video when outside an episode folder)")
    a = ap.parse_args()
    if a.cmd == "upload":   # 上傳前先過出片清單（在連線與讀權杖之前）；其他子指令不經過
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "checklist"))
        import checklist
        checklist.gate(a.video, "release", a.skip_checklist, "upload", outside_ok=False)   # 集資料夾外的片檢查不了：要寫原因

    if a.cmd == "scopes":   # 直接拿 refresh token 換權杖，看 Google 實際給的範圍（讀取 API 驗不出缺管理權限）
        import requests
        t = json.loads(TOKEN.read_text()) if TOKEN.exists() else sys.exit("✗ no token: run auth first")
        r = requests.post(t["token_uri"], data={"client_id": t["client_id"], "client_secret": t["client_secret"],
                                                 "refresh_token": t["refresh_token"], "grant_type": "refresh_token"}).json()
        got = set(r.get("scope", "").split())
        miss = set(SCOPES) - got
        if got:
            print(f"scopes: {' '.join(sorted(got))}")
        else:   # 不印整個回應：裡面可能有存取權杖，而開工清單會把這段輸出寫進 nightly/checklist_release.json
            err = " ".join(str(x) for x in (r.get("error"), r.get("error_description")) if x)
            print(f"scopes: {err or 'no scope in the response'}")
        sys.exit(f"✗ missing scopes {' '.join(miss)}: rerun auth" if miss else 0)
    yt = build("youtube", "v3", credentials=creds(interactive=a.cmd == "auth"))
    if a.cmd in ("auth", "whoami"):
        ch = yt.channels().list(part="snippet", mine=True).execute().get("items", [])
        print(json.dumps([{"id": c["id"], "title": c["snippet"]["title"]} for c in ch], ensure_ascii=False))
        return

    if a.cmd == "thumb":
        sys.exit(1 if set_thumb(yt, a.video_id, a.image) else 0)   # set_thumb already printed why

    if a.cmd in ("show", "desc"):
        items = yt.videos().list(part="snippet,status", id=a.video_id).execute().get("items", [])
        if not items:
            sys.exit(f"✗ video not found: {a.video_id}")
        sn, st = items[0]["snippet"], items[0]["status"]
        if a.cmd == "desc":   # snippet 要整包送回，少了 title／categoryId 會被拒；只換 description，不碰 status
            keep = {k: sn[k] for k in ("title", "tags", "categoryId", "defaultLanguage", "defaultAudioLanguage") if k in sn}
            keep["description"] = open(a.desc_file, encoding="utf-8").read().strip()
            sn = yt.videos().update(part="snippet", body={"id": a.video_id, "snippet": keep}).execute()["snippet"]
        print(json.dumps({"id": a.video_id, "title": sn["title"], "tags": sn.get("tags", []), "categoryId": sn.get("categoryId"),
                          "language": sn.get("defaultLanguage"), "privacy": st["privacyStatus"], "publishAt": st.get("publishAt"),
                          "description_head": sn["description"][:160]}, ensure_ascii=False))
        return

    if a.cmd == "private":   # 重傳之後：舊的那支改私人、不排定（不刪）
        items = yt.videos().list(part="status", id=a.video_id).execute().get("items", [])
        if not items:
            sys.exit(f"✗ video not found: {a.video_id}")
        st = items[0]["status"]
        st["privacyStatus"] = "private"
        st["publishAt"] = None   # 送 null 才會清掉排程；不帶這個欄位 API 會保留原本的時間（實測）
        yt.videos().update(part="status", body={"id": a.video_id, "status": st}).execute()
        for _ in range(6):   # update 的回應與剛重讀的狀態都可能還帶舊 publishAt，約幾秒後才清掉（實測）
            time.sleep(5)
            r = yt.videos().list(part="status", id=a.video_id).execute()["items"][0]["status"]
            if not r.get("publishAt"):
                break
        print(json.dumps({"id": a.video_id, "privacy": r["privacyStatus"], "publishAt": r.get("publishAt")}, ensure_ascii=False))
        if r["privacyStatus"] != "private" or r.get("publishAt"):
            sys.exit("✗ still public or still scheduled; change it by hand in YouTube Studio")
        return

    if a.cmd == "plswap":   # 換片：上傳時新片接在清單最後，順序會亂，所以把新片放到舊片的位置再移掉舊片
        for pl in [x for x in a.playlists.split(",") if x]:
            items, tok = [], None
            while True:
                r = yt.playlistItems().list(part="snippet", playlistId=pl, maxResults=50, pageToken=tok).execute()
                items += r.get("items", []); tok = r.get("nextPageToken")
                if not tok:
                    break
            vid = lambda it: it["snippet"]["resourceId"]["videoId"]
            old = [it for it in items if vid(it) == a.old_id]
            new = [it for it in items if vid(it) == a.new_id]
            if not old or not new:
                sys.exit(f"✗ playlist {pl}: old video {'present' if old else 'absent'}, new video {'present' if new else 'absent'}; nothing changed")
            pos = old[0]["snippet"]["position"]
            n = new[0]
            try:
                yt.playlistItems().update(part="snippet", body={"id": n["id"], "snippet": {
                    "playlistId": pl, "resourceId": n["snippet"]["resourceId"], "position": pos}}).execute()
            except HttpError as e:   # 清單排序不是「手動」時不能指定位置（清單自己會排），只移出舊片
                if "manualSortRequired" not in str(e):
                    raise
                pos = "auto"
            yt.playlistItems().delete(id=old[0]["id"]).execute()   # 只移出清單，影片本身不刪
            print(json.dumps({"playlist": pl, "position": pos, "new": a.new_id, "removed": a.old_id}, ensure_ascii=False))
        return

    body = {"snippet": upload_snippet(a.title, Path(a.desc_file).read_text(encoding="utf-8"), a.tags, a.category, a.language),
            "status": {"privacyStatus": a.privacy, "selfDeclaredMadeForKids": False, **({"containsSyntheticMedia": True} if a.synthetic else {})}}
    if a.publish_at:   # publishAt 只能配私人（API 規定）；時間已過就停，不自動延
        from datetime import datetime, timedelta, timezone
        at = datetime.fromisoformat(a.publish_at)
        if at.tzinfo is None or at <= datetime.now(timezone.utc) + timedelta(minutes=15):
            sys.exit(f"publish time {a.publish_at} has passed, is too close or has no time zone: nothing uploaded; decide whether to postpone or publish directly")
        a.privacy = "private"; body["status"] |= {"privacyStatus": "private", "publishAt": at.isoformat()}
    req = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(a.video, chunksize=8 << 20, resumable=True))
    res = None
    while res is None:
        st, res = req.next_chunk()
        if st:
            print(f"  {int(st.progress() * 100)}%", file=sys.stderr)
    vid = res["id"]
    thumb_err = set_thumb(yt, vid, a.thumb) if a.thumb else None
    for pl in [x for x in a.playlist.split(",") if x]:   # 主清單＋分部清單（series.py playlists）
        yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": pl,
                                  "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
    hit = checklist.find_episode(a.video)   # 字幕檔手動傳：印出要傳哪幾個（結果那一行 JSON 維持在最後一行）
    if hit:
        try:
            text = checklist.items.caption_hint(hit[0])
        except Exception as e:
            text = f"cannot print the subtitle file list: {type(e).__name__} {e}"
        if text:
            print(text)
    got = res.get("status", {}).get("privacyStatus")
    print(json.dumps({"id": vid, "url": f"https://youtu.be/{vid}", "privacy": got, "publishAt": res.get("status", {}).get("publishAt"),
                      "locked_private": got == "private" and a.privacy != "private",
                      **({"synthetic": res.get("status", {}).get("containsSyntheticMedia")} if a.synthetic else {}),
                      **({"thumb": thumb_err or "ok"} if a.thumb else {})}, ensure_ascii=False))


if __name__ == "__main__":
    main()
