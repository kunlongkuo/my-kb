# Changelog

## 1.1.4 (2026-11-21)

### Generated shots: Google Flow joins VideoExpress and H3

With a Google AI Plus, Pro or Ultra plan, a single shot can come from Google Flow (Omni 1.2 Flash, Veo). The new
`google-flow` skill drives Flow in your own signed-in Chrome, because Google refuses sign-in in browsers launched by
automation tools. `skills/google-flow/scripts/flow_ingest.py` puts the download at `ve_<look>/shotK.mp4` with a
`.flow.json` record (model, settings, prompt, source file, SHA-256) and a ten-frame sheet to look at before cutting.
`references/flow-video.md` holds the steps and what was measured: a reference image keeps faces and clothes, one
continuous action with one camera path flows better than timed blocks, selfie vlogs and bullet time work, large
martial-arts scenes do not, and which wording gets refused by policy.

### Music: a song from Google Flow Music

The same skill makes a song or an instrumental in Flow Music (included in Google AI Pro) from your lyrics and a style
line, and `flow_ingest.py --doc` sets it as the film's `bgm` with its credit. `references/flow-music.md` covers the
Compose panel, how to write the style line (describe a singer's style instead of naming them), and what the terms
do and do not say about commercial use.

### VideoExpress runs no longer stop on a late candidate

When VideoExpress adds a second candidate frame after `--auto-pick` has chosen the first, the run now keeps the
frame VideoExpress has selected, as long as it was made for this shot, instead of stopping the whole batch. A frame
left over from the previous shot still stops it.

## 1.1.2 (2026-11-20)

- **Every exported film is checked.** Concat exports run `tools/nightly/film_check.py`: length, black frames, loudness,
  sound effects in the mix, stale files. The release checklist uploads only the checked file.
- **Reminders that never fail a film:** too many generated shots (`peak_weight`), too close to the last three
  episodes (`vs_prev`), music that does not step aside (`quiet`), a slow opening (`first30`), the same theme three
  episodes in a row.
- **Side by side with a film you like:** `tools/sample/breakdown.py`.
- **New scene moves:** a quotation that comes out of a blur as it is read (`quote_card` `reveal`), a struck-out word
  rewritten (`formula` `strike.to`), a long timeline that slides (`timeline` `window` / `from`), a clue board
  (`relation` `look: "board"`).
- **Five new themes:** `dark-gold`, `newsroom`, `vintage-poster`, `editorial-serif`, `cinematic-dark`, each changing
  colours, shapes and ground (`themes/styles.json`).
- **Theme preview:** `doc_theme_preview.py` plays three themes on the episode's own beats before it is voiced
  (`docs/FLOW.md` optional G).
- **Optional fonts:** LXGW WenKai (TC and SC) and jf open-huninn, listed with their download links.
- **Local transcription is whisper.cpp** (set `S2F_WHISPER_CPP_MODEL`; `setup_voice.sh` does it).
- **Fixes:** an all-silent sound track no longer crashes the film check.

## 1.1.0 (2026-11-18)

- **MiniMax H3 and MiniMax Music 3 on your own Google Colab GPU (optional).** `tools/h3/h3_film.py` plans, runs and
  collects generated shots and a lip-synced host (the host keeps the narration as its voice); `tools/music3/music3_film.py`
  makes a song or an instrumental for `bgm.src`. The H3 licence excludes the US, the EU, the UK and South Korea, so
  the start checklist asks where you are and where the film is used (`h3-territory`).
- **Dialogue voices.** `lines[].speaker` picks a voice from `doc.json` `"voices"`, each with its own pitch; the
  speaker is part of the approved script.
- **Subtitles.** `subs.burn: "en"` burns English subtitles only over Chinese narration; an empty `"en"` line gives no
  English cue; `sub_highlight` colours chosen words in burned subtitles.
- **The picture runs on after the last word.** `end_hold` (default 1 s) keeps the last picture on screen so a face
  can settle; the host's last part ends in that silence too.
- **Host takes.** `clip_in` keeps lip sync when the narration was retimed after the host was made; TalkingPhotos
  segment names follow what TalkingPhotos shows (an underscore becomes a space).
- **Website.** The opencode + DeepSeek V4.1 Flash trial on the homepage; share previews in Chinese and English.
- **README.** Rewritten after the website: what is different, what it does with real frames, films made with it, the
  agent trials and the first film in three steps.

## 1.0.0 (2026-11-17)

The first public release of Script2Film: from a script to a finished, checked explainer film on your own Mac, with no
account and no API key for the core flow.

- **Core flow.** Script (`doc.json`) → voice (Qwen3-TTS, local) → word timing and subtitles (mlx-whisper, local) →
  27 scenes drawn by code → cut (`doc_cut.py --render`) → delivery check (`tools/nightly/check.py`: loudness, peak,
  length, a frame sheet, and reports of stalled pictures, empty cards and blank openings).
- **The script is approved before the voice.** `doc_tts.py` voices only a script the user has approved
  (`--script-approved`); `AGENTS.md` says what counts as approval.
- **Agents.** `AGENTS.md` and the `script2film` and `ve-director` skills, linked for Claude Code and other agents.
  Claude Code, Google Antigravity and opencode (with a local Qwen model and with DeepSeek) have each made films from
  the documents alone (`docs/AGENT-TRIALS.md`).
- **Optional stages.** Generated shots on VideoExpress (`tools/ve-runner/`), a talking host on TalkingPhotos
  (`tools/tp/`), composed music (`tools/score/`), Concat projects (`tools/concat/`), YouTube upload
  (`tools/youtube/`). Each spends your own account's credits only when you say so.
- **Examples.** `examples/coffee` (English, code-drawn only) and `examples/brewing` (Chinese, with a generated shot
  and a host; `premade/` makes it work without accounts).
- **Install.** `docs/INSTALL.md` and `tools/doctor/doctor.py`; verified on Apple Silicon Macs only.

Versions 0.7.0 to 0.9.0 were releases of Prompt Studio, the single-page prompt builder this project started as. It
now lives in `tools/prompt-studio/`; its history is not part of this repository.
