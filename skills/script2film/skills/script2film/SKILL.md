---
name: script2film
description: Use when the user wants a narrated explainer video made from a script or a topic — 解說片、旁白短片、知識型影片、把稿子做成影片、explainer、narrated video, voice-over with charts and subtitles. Runs the Script2Film flow in this repository (script → cloned or designed voice → timing → code-drawn scenes → cut → check). For VideoExpress storyboards and acted story films use ve-director instead.
---

# Script2Film

Turn a script into a narrated explainer film with this repository's tools. This file routes; the steps live in `docs/FLOW.md`.

Paths below are from the repository root. Reply in the language the user writes in.

## When this applies

- The user has a script, an article or a topic and wants a narrated film with subtitles and drawn scenes (charts, lists, quotes, maps).
- A VideoExpress storyboard, T2I / I2V prompts, or an acted story film: use `skills/ve-director/SKILL.md`.
- One clip from Google Flow (Omni, Veo) or a song from Google Flow Music in the user's own Google AI account: use `skills/google-flow/SKILL.md`.

## Before anything else

Run `python3 tools/doctor/doctor.py`. Fix each `✗` with the line printed under it. On a new machine follow `docs/INSTALL.md`; ask the user before the long step (`setup_voice.sh`, about 20 minutes and 6 GB) and run it in the background. If something cannot be fixed (a missing model, a missing program), stop and tell the user what is missing.

## The flow

Follow `docs/FLOW.md` step by step. Read the section of the step you are on, and the document it names, when you get there; do not read everything first.

| Step | What | Read |
|---|---|---|
| F0 | install check | `docs/FLOW.md` F0, `tools/doctor/README.md` |
| F1 | script and `doc.json` | `docs/FLOW.md` F1, `skills/ve-director/doc/README.md` (doc.json fields and scenes) |
| F2–F5 | voice, timing, scenes, cut | `docs/FLOW.md` F2–F5 |
| F6 | check the film | `docs/FLOW.md` F6 |
| optional | generated shots, host, music, Concat, checklist, upload | `docs/FLOW.md` Optional A–F and the README each names |

First time in this repository: make `examples/coffee` first (`examples/coffee/README.md`). It needs no account and no key. To see generated shots and a host joined in without an account, make `examples/brewing` next (`examples/brewing/README.md`, the premade path).

## Stop and wait for the user

1. After F1: show the full narration and the beat table and wait for the user's answer. Do not change the narration afterwards. Approval is the user's yes to this script, after reading it. The only other case: before you started, the user said in so many words that they do not need to see the script before the voice is made; then show it to them anyway and go on. "Make me a film", "do it all and report back" and "don't ask me questions" are not approval. When the user is away, stop at F1 with the script saved (`doc.json`, and `facts.md` when there is one) and tell them it is waiting for their OK. `doc_tts.py` makes no voice without approval (exit code 4); pass `--script-approved` only after the user has approved this script, never for them. This does not loosen the rules on spending credits, uploading or publishing.
2. Before sending anything to VideoExpress or TalkingPhotos: it spends the user's generation credits. For a host, the user also picks the look image first; a photo they hand you is reference material, not the finished look (`docs/FLOW.md`, Optional B).
3. Before uploading, publishing, scheduling or deleting a video.
4. Before switching to cloud transcription (`"asr": "cloud"`): the narration audio goes to Groq and ElevenLabs.

## Do not

- Type the user's account names or passwords. On a login page, stop and ask the user to log in.
- Put keys in code, in `config.json` or in a project folder. Keys go in `~/.config/script2film/secrets.json` or the environment.
- Send a real person's photo to a video model, or use news-agency or broadcaster photos and footage.
- Deliver or upload a film that fails `tools/nightly/check.py`.
- Bypass the checklist with `--skip-checklist` without the user's agreement and a written reason.
