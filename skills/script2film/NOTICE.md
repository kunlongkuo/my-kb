# NOTICE

Script2Film is MIT-licensed (see `LICENSE`). This file records the code and text adapted from other projects, the licence of each
third-party component the workflow uses, and where the bundled assets came from. Licences were checked on the dates given.

## Adapted code and text

| Source                   | Licence (how checked)                                                                     | What was taken                                                                                                                  | Where it is here                                                                                                                                               |
| ------------------------ | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| POUND0423/AI-drama-pound | MIT (GitHub API, 2026-11-17; upstream LICENSE copied to `tools/prompt-studio/LICENSE.AI-drama-pound`) | adapted text: the screenwriting rules are condensed from it                                                                     | `tools/prompt-studio/prompt-studio.html` (and its website copy `docs/studio/app.html`), `tools/prompt-studio/README.md`, `tools/prompt-studio/README.zh-TW.md` |
| alchaincyf/huashu-motion | MIT (GitHub API, 2026-11-13; upstream LICENSE copied to `tools/qa/LICENSE.huashu-motion`) | adapted code: `tools/qa/motion-qa.mjs` is ported from its `cli/lib/qa.js`; elsewhere it is only mentioned as a set of templates | `tools/qa/motion-qa.mjs`, `skills/ve-director/doc/formats/vox-host/FORMAT.md`                                                                                  |

## Third-party components

Not shipped in this repository; you install them, they come from npm, or (ElevenLabs Scribe) they are an online service called with your own key.

| Component | Licence (checked 2026-11-12) | How it is used |
|---|---|---|
| GSAP 3.12.2 | GSAP Standard "no charge" licence (not an OSI licence; terms at <https://gsap.com/community/standard-license/>, read 2026-11-15) | an npm dependency in the root `package.json`, installed by `npm ci`; the scripts copy `gsap.min.js` next to each rendered page; not shipped in this repository |
| HyperFrames | Apache-2.0 | renders scene pages to video; installed with npm. Two thresholds are taken from its embedded-captions skill: silence at −35 dB for 0.6 s (`tools/qa/hallucination_guard.py`) and subtitles shorter than 0.5 s / 0.8 s (`doc_common.short_cues`); the code is our own |
| Concat | AGPL-3.0-or-later | assembly; installed by the user and driven through its local API, not modified |
| Qwen3-TTS | code Apache-2.0; model weights `Qwen3-TTS-12Hz-1.7B-Base` and `-VoiceDesign`: apache-2.0 (Hugging Face model index, 2026-11-15) | narration voice; installed by the user |
| whisper.cpp | code MIT (<https://github.com/ggml-org/whisper.cpp>, read 2026-11-20); model weights `ggml-large-v3-turbo.bin` from `ggerganov/whisper.cpp`: mit (model card `license` field, <https://huggingface.co/ggerganov/whisper.cpp>, read 2026-11-20), converted from `openai/whisper-large-v3-turbo`: mit | transcription and word timing; installed by the user (`setup_voice.sh`); the weights are downloaded, not shipped |
| demucs | code MIT; model weights: the author states their licence is unclear | optional vocal removal |
| OpenCC | Apache-2.0 | Simplified to Traditional Chinese |
| GeneralUser GS SoundFont (v2.0.3) | its own licence v2.0, read 2026-11-14 at <https://github.com/mrbumpy409/GeneralUser-GS> (`documentation/LICENSE.txt`): "You may use GeneralUser GS without restriction for your own music creation, private or commercial" and "Please feel free to use it in your software projects". The author also states he "cannot be 100% sure where all of the samples originated" | instrument sounds for `tools/score/`; downloaded by the user, not shipped here for that reason and for its size (32 MB) |
| tinysoundfont | MIT (PyPI classifier, read 2026-11-14; PyPI lists no project page, so no licence file was read) | renders the score offline; installed by `uv sync` in `tools/score/` |
| librosa, soundfile | ISC, BSD-3-Clause (PyPI, read 2026-11-14) | audio analysis and wav files in `tools/score/` and `tools/tts/` |
| Playwright | Apache-2.0 | drives Chrome for page checks and VideoExpress |
| google-api-python-client, google-auth, google-auth-oauthlib, google-auth-httplib2 | Apache 2.0 (`pip show`, 2026-11-13) | `tools/youtube/`: upload, schedule and retitle on the user's own channel; installed by the user |
| requests | Apache-2.0 (`pip show`, 2026-11-13) | `tools/youtube/` |
| speechbrain | Apache-2.0 (upstream LICENSE read 2026-11-13) | `tools/tts/speaker_sim.py`: speaker similarity; installed by the user |
| speechbrain/spkrec-ecapa-voxceleb (model) | apache-2.0 (Hugging Face model index, 2026-11-13) | downloaded by speechbrain on first run of `speaker_sim.py`; not shipped |
| ElevenLabs Scribe API | online service under its terms of service (see the official page) | optional cloud word timing ("asr": "cloud"); sends the whole narration audio; no code or model shipped |

Fonts, downloaded by the user (not in this repository; `assets/README.md`):

| Asset | Licence | Note |
|---|---|---|
| Noto Sans TC, Noto Serif TC | SIL OFL 1.1 | the licence text travels with the fonts |
| LXGW WenKai TC, LXGW WenKai (optional) | SIL OFL 1.1 (upstream repository, read 2026-11-20) | downloaded from the lxgw GitHub releases |
| jf open-huninn 2.1 (optional) | SIL OFL 1.1 (upstream README, read 2026-11-20) | downloaded from the justfont GitHub release |

Sound effects, in this repository (`assets/sfx/`; each file's licence is also in `assets/sfx/manifest.json`):

| Asset | Licence | Note |
|---|---|---|
| Kenney sound packs | CC0 (as recorded in the sound library manifest) | interface, impact, UI and RPG packs; files are in `assets/sfx/` (`kenney-*`) |
| Self-made sounds | same licence as the repository | five sounds synthesized with ffmpeg by `skills/ve-director/doc/scripts/sfx_seed.py`; files are in `assets/sfx/` (`self-*`) |
| VideoExpress-generated sounds | released by the author with this repository (MIT) | 28 sounds generated by the project author with VideoExpress AI Sound Maker (Sound From Prompt), from the English prompts kept in each entry's `query`; files are in `assets/sfx/ve-gen/`. Sounds you generate yourself with `tools/assets/gen_sfx_ve.py` go to your own folder, not here |

Example files, in this repository:

| File | Licence | Note |
|---|---|---|
| `examples/coffee/refs/narrator.wav` | made for this project; same licence as the repository | a synthetic English reference voice designed from a text description with Qwen3-TTS VoiceDesign (`tools/tts/design_voices.py`); not a recording or a clone of any real person; the description and seed are in `examples/coffee/refs/voice_cast.json` |
| `examples/brewing/refs/narrator.wav` | made for this project; same licence as the repository | a synthetic reference voice designed from a text description with Qwen3-TTS VoiceDesign; not a recording or a clone of any real person; the description and seed are in `examples/brewing/refs/voice_cast.json` |
| `examples/brewing/premade/tts/voice.wav` | made for this project; same licence as the repository | the example's narration, spoken by that synthetic voice with Qwen3-TTS |
| `examples/brewing/refs/host_look.jpg` | generated by the project author with VideoExpress (text to image, no reference photo); provided only for trying this example | a fictional person, not a likeness of anyone. VideoExpress, videoexpress.ai, read 2026-11-16: "Rest assured, you retain full ownership rights to the videos you craft"; its terms set no limit on how outputs are distributed and give no explicit redistribution licence |
| `examples/brewing/premade/ve_flat/shot1.mp4` | generated by the project author with VideoExpress; provided only for trying this example | a flat illustration of a cafe counter, no people; same source note as above |
| `examples/brewing/premade/host/parts/part1.mp4` | generated by the project author with TalkingPhotos from `host_look.jpg` and the narration above; provided only for trying this example | TalkingPhotos terms, talkingphotos.ai/terms/terms.php, read 2026-11-16, section 2: the user is "solely responsible for all images, videos, audio, prompts, text, and other materials you upload, submit, generate, or distribute through the Service"; no limit on distribution and no explicit redistribution licence |

Website images and clips, in `docs/site/`:

| File | Source | Note |
|---|---|---|
| `scenes/*`, `palettes/*`, `beat-pie.*` | rendered by this project's scene code with made-up sample data | same licence as the repository |
| `subtitles.jpg`, `check-sheet.jpg`, `shot-generated.jpg` | frames and the check sheet from `examples/coffee` and `examples/brewing` | see the example files above |
| `hero.mp4`, `hero-poster.jpg`, `work-1.jpg` | a silent excerpt, a frame and the thumbnail of the project author's short film "When You Meet a Love Negotiator" (youtu.be/qrFl_yrWPNk), generated with VideoExpress | fictional characters, not likenesses of anyone; shown to demonstrate the project, not offered for reuse |
| `host-*.jpg`, `scene-prompt.jpg`, `work-4.jpg` | frames and the thumbnail of the project author's tutorial "One Prompt, a 5-Shot Kung Fu Fight" (youtu.be/1aTJSye-l38) | they show the author's own likeness and channel mark; shown to demonstrate the project, not offered for reuse |
| `work-2.jpg`, `work-3.jpg` | thumbnails of two other videos on the author's channels | shown to demonstrate the project, not offered for reuse |
| `studio-hero.mp4`, `studio-hero-poster.jpg`, `studio-work-1.jpg` | a silent excerpt, a frame and the thumbnail of the project author's short film "Dino park" (youtu.be/fKrBTTZsiMM), generated with VideoExpress from prompts written in Prompt Studio | shown to demonstrate the project, not offered for reuse |
| `studio-work-2.jpg`, `studio-work-3.jpg` | thumbnails of the project author's films "Blue Collar Hero Heavy Duty" (youtu.be/UfWb6C3dOAM) and "馬偕博士動畫" (youtu.be/FjaXYLEwLHI), generated with VideoExpress from prompts written in Prompt Studio | shown to demonstrate the project, not offered for reuse |
| `studio-app.png`, `studio-app-en.png` | screenshots of this repository's `tools/prompt-studio/prompt-studio.html` | same licence as the repository |
| `og.jpg` | the share-preview image, made by `tools/site/make_og.py` from `hero-poster.jpg` (see above) with the name and subtitle drawn in Noto Sans TC (`assets/fonts/`) | the background frame is shown to demonstrate the project, not offered for reuse |
