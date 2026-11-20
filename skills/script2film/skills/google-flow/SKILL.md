---
name: google-flow
description: Use when the user wants a video clip made in Google Flow (Omni, Veo) or a song or instrumental made in Google Flow Music (Lyria), with their own Google AI Plus / Pro / Ultra subscription — Flow、Flow Music、Omni、Veo、Lyria、用 Google AI Pro 做影片、做歌、做配樂、vlog 邊走邊講、子彈時間. Drives the user's own signed-in Chrome (Claude in Chrome), then moves the download into the project with a provenance record. For VideoExpress shots use ve-director; for music on Colab use tools/music3.
---

# Google Flow and Flow Music

Make one video clip or one song in the user's Google account and bring it into a Script2Film project. Neither site has an API for this, and Google refuses sign-in in a browser launched by automation tools (tested 2026-11-21: "This browser or app may not be secure"). So the work happens in the user's own Chrome through the Claude in Chrome extension. Do not try to get round that sign-in check (no stealth flags, no copied cookies); if Claude in Chrome is not available, stop and tell the user.

Paths are from the repository root. Reply in the language the user writes in.

## Read

| For | Read |
|---|---|
| a video clip | `references/flow-video.md` (steps, prompt writing, failures) |
| a song or instrumental | `references/flow-music.md` (steps, the Sound line, rights) |
| browser tools | the Claude in Chrome skill: load its tools in one call, work in a new tab |

## Steps

1. **Job sheet first.** Write down before opening the site: what it is for (which project, which shot or `bgm`), model, aspect ratio, length, number of outputs, the prompt (for music: Sound line and lyrics), and where the file goes. Save the prompt to a text file in the project; it goes into the provenance record.
2. **Spend.** Tell the user what it costs before sending: Flow shows the credits on the settings chip; Flow Music uses its own credits. A clear request from the user ("make this with Flow") is the go-ahead for that job; each retry after a refusal is a new job and is named in your report.
3. **Submit in the user's Chrome**, one tab per site. The user signs in (a sign-in page, 「使用 Google 帳戶繼續」, a password or a code: stop and ask). Welcome pages, the privacy-policy page, feature tours and the per-upload image-rights confirmation are first-use dialogs: handle them only if the user has said you may; otherwise ask once and let them click.
4. **Wait without polling hard.** A 10 s clip takes one to two minutes, a song under a minute. Check with a screenshot every 20–30 s, or do other work in between.
5. **Download one file at a time** and confirm it landed in `~/Downloads` before the next. If nothing arrives, Chrome may be blocking automatic downloads for the site: that is a browser setting, so ask the user.
6. **Ingest** with `skills/google-flow/scripts/flow_ingest.py` (`--latest video|music --to <file> --model … --settings … --prompt-file …`, `--doc` for music). It moves the file, writes `<file>.flow.json` (model, settings, prompt, source name, SHA-256, length, notice) and, for a video, `<file>.sheet.jpg`.
7. **Check before using.** Look at the sheet (face and clothes kept, nothing deformed, no text) or have the user listen. Video clips then follow `docs/FLOW.md` Optional A "Using another platform for the shots"; music follows Optional C.
8. **Report**: the files, the credits spent, refusals and retries, and anything the user should watch or listen to themselves (speed and impact of action, lip sync, melody: frames cannot judge these).

## Do not

- Type the user's password, a code, or card details; accept terms for them without their say-so; change Chrome or account settings.
- Upload a real person's photo or someone else's image as a reference, or name a real singer or actor in a prompt.
- Retry a refused prompt unchanged.
- Leave a downloaded file in `~/Downloads` as the project's source: ingest it.
- Publish without labelling the film as AI-generated (`--synthetic`).

## Tests

`python3 -m pytest -q skills/google-flow/tests` (the ingest script; no network).
