# Making an explainer film: the flow

The general version: anyone, or any AI agent, can follow it to turn a script into an explainer film with narration, subtitles and pictures.
F0 to F6 are the path that costs nothing (voice and transcription on this machine, scenes drawn by code) and were checked with `examples/coffee`. The optional sections need outside accounts or other programs and were not checked with the example.

Conventions: `<project>` is the folder that holds `doc.json`. **Run every command from the repository root** (all paths are written relative to it).
Where to put a project: outside the repository, or under `examples/<name>/` (what the steps write there is ignored by git; `git clean -fdX examples/<name>` removes it).

| Step | What | Required | Stop and ask |
|---|---|---|---|
| F0 | Install check | yes | when a `✗` cannot be fixed |
| F1 | Script and `doc.json`, lint | yes | **show the narration and the beat table; continue only when the user approves this script** (`doc_tts.py` will not run without it) |
| F2 | Voice, pick the takes | yes | |
| F3 | Timing | yes | |
| F4 | Scenes drawn by code | yes | |
| F5 | Cut | yes | |
| F6 | Check the film | yes | numbers fail: do not deliver |
| Optional A | Generated shots (VideoExpress, or MiniMax H3 on Colab) | | **ask before sending**; the user logs in |
| Optional B | Host (TalkingPhoto, or MiniMax H3 on Colab) | | **the user picks the look image; ask before sending**; the user logs in |
| Optional C | Music and sound effects (or a song from MiniMax Music 3 on Colab) | | |
| Optional D | Final film in Concat | | |
| Optional E | Start and release checklists | | answer truthfully; ask the user when you do not know |
| Optional F | Upload to YouTube | | **upload, publish, schedule or delete only when the user says so** |
| Optional G | Theme preview | | show it with the script at F1; the user picks |

The steps are numbered, but not every step waits for the one before it: optional A can be sent when F2 starts, and optional B runs alongside A once F2 is done.

## F0 Install check

```bash
python3 tools/doctor/doctor.py
```

Right: the last line says you can start (`✓ ready to go`) and the exit code is 0. The line under each `✗` (starting with `→`) is the fix; do it and run again. The script only checks: it installs and downloads nothing.
On a new machine the whole installation, in order and with measured times, is in `docs/INSTALL.md`: about 30 minutes and 7 GB the first time. The slow step is `bash tools/doctor/setup_voice.sh` (about 20 minutes, mostly silent); run it in the background with its output in a file and look at the file now and then. **Ask the user before starting it.**
The Python packages live in the project's own `.venv`; keep typing `python3` as written here, the scripts restart themselves with `.venv`'s Python.
`npm ci` (step 4 of `docs/INSTALL.md`) may print `npm warn deprecated …` lines and end with `npm warn install-scripts <n> packages have install scripts not yet covered by allowScripts`: newer npm versions (11.19 here) skip dependencies' install scripts unless `package.json` approves them. Ignore it; there is no need to approve them: with those scripts skipped, the tests and a full render of `examples/brewing` passed (2026-11-17). The exit code is 0.
A fresh clone has no font files (the two Noto fonts are not in git); the check prints the two download commands. See `assets/README.md`.
Playwright's own headless browser is a separate download too (step 3 of `docs/INSTALL.md`, about 97 MB); without it the check prints `.venv/bin/python -m playwright install --only-shell chromium`.
Paths live in `~/.config/script2film/config.json` (one per machine, described in `tools/doctor/README.md`). For the optional features add `--need concat,ve,tp,youtube` so those groups count as required too.

**Running inside an agent with a sandbox.** Some agents run commands in a sandbox that blocks network access, files outside the workspace and local connections by default. This project needs all three allowed:

1. **Network access**, while installing (the fonts, the npm and Python packages, HyperFrames' browser and the voice model are downloaded) and the first time F2 transcribes (the transcription model, about 1.5 GB, is downloaded then).
2. **Reading and writing the voice and transcription environments**, which live outside the repository (`~/s2f-voice/` by default). Their paths are the two keys `S2F_QWEN_TTS_DIR` (a folder) and `S2F_WHISPER_CPP_MODEL` (the transcription model file) in `~/.config/script2film/config.json`; the voice step (F2) runs the voice environment's own Python, the timing step (F3) runs `whisper-cli`.
3. **Connections to this machine (127.0.0.1)**: HyperFrames renders each scene by serving the page from a small web server on this machine to its headless browser.

When one is blocked: the font and package downloads fail (1); the voice or transcription step stops because that environment's Python cannot read its own `pyvenv.cfg` (2); the scene render stops with `connect EPERM 127.0.0.1` (3). Allow these three for this workspace and run the step again; nothing else needs to change.

**Running with a local model as the agent.** Raise the model's context window well above a default such as 8192 tokens. `AGENTS.md`, this file and `skills/script2film/SKILL.md` alone are about 5,500 words (roughly 8,000 to 9,000 tokens), so a small window cannot hold them together with a long conversation, and each later step gets slower. Ask for one film at a time.

## F1 Script and doc.json

`doc.json` holds the narration (`lines`), the beats (`beats`: which lines go with which picture), the palette (`theme`) and the reference voice (`voice`). The fields and each scene's parameters are in `skills/ve-director/doc/README.md`; the smallest example is `examples/coffee/doc.json`.

```bash
python3 skills/ve-director/doc/scripts/doc_lint.py <project>/doc.json
```

Right: exit code 0 and the line `doc_lint: ok`. Lines starting with `⚠` are notes and do not stop anything. For a script the user has not approved yet, one more line follows: `Next: show the user the narration and the beat table …`.

**Stop**: show the user the full narration and the beat table (for each beat: which lines, which picture) and wait for their answer. Do not change the narration afterwards.
Approval is the user's yes to this script, after reading it. The only other case: before you started, the user said in so many words that they do not need to see the script before the voice is made; then show it to them anyway and go on. "Make me a film", "do it all and report back" and "don't ask me questions" are not approval. When the user is away, stop at this step with the script saved (`doc.json`, and `facts.md` when there is one) and tell them it is waiting for their OK. This does not loosen the rules on spending credits, uploading or publishing.
The program holds this stop: `doc_tts.py` (F2) makes no voice for a script without approval (below).

Quoted scripture: when `doc.json` has a `facts` list, `doc_lint.py` compares each quote with the excerpt written in `facts.md` and prints a reminder that nothing here reads a full Bible text. The excerpts are only as right as whoever typed them: copy them from a Bible, not from memory, and show the user every quote with its reference at this stop. The `facts.md` table, what needs a row and an English example: "facts.md" in `skills/ve-director/doc/README.md`.

Reference voice: `voice.ref_wav` is about 10 seconds of clean speech and `voice.ref_text` is its word-for-word text. Using a real person's voice needs that person's consent. Without one, design a voice that belongs to nobody: `design_voices.py` in `tools/tts/README.md`.
When the user names no voice, you can keep the synthetic voice an example ships with: `examples/coffee/refs/narrator.wav` (English, a woman's voice) or `examples/brewing/refs/narrator.wav` (Taiwanese Mandarin, a man's voice), each with its `narrator.txt`; copy both files into the project's `refs/`. They were designed from a text description and are not a recording or a clone of any real person (`NOTICE.md`). A real person's voice still needs that person's consent.

## F2 Voice, pick the takes

```bash
python3 skills/ve-director/doc/scripts/doc_tts.py <project>/doc.json --script-approved   # only after the user approved this script (F1)
python3 skills/ve-director/doc/scripts/doc_voice.py <project>/doc.json
```

`--script-approved` says the user has seen the narration and the beat table and said yes to this script. Pass it only then; passing it for the user is reporting an approval that was not given. It is recorded in `<project>/script_approval.json` with a fingerprint of the narration, so a later run on the same narration needs no flag; change any line and the first command stops again until the user approves the new version. The bundled examples, unchanged, count as approved and run without the flag.
Without approval the first command makes no voice, prints what to show the user, and exits with code 4, before loading the voice model. That is not a failure to fix: go back to the stop at F1.

The first command needs the voice model's own Python environment; started with any `python3`, it re-runs itself there and prints one line saying so (the folder is `S2F_QWEN_TTS_DIR` in the config file). It records three takes of every line into `<project>/tts/`. The second command transcribes every take, picks the one closest to the script and joins them into `<project>/tts/voice.wav`.

Right: both exit 0, and the second ends with a line like `narration 23.7s, 4 lines; lowest 1.00; below 0.85: none` (the numbers differ a little every run). `sox: command not found` from the first command comes from the voice model's own environment and can be ignored (the takes are still written). When a line is below 0.85, look at `heard` for that line in `tts/lines.json`: it is usually a homophone (the transcriber's choice, not a misreading). If it really was misread, run the first command again with `--force`. If it fails again, stop and report.

With `"asr": "cloud"` in `doc.json`, this step and the next send the narration audio to Groq and ElevenLabs and need both keys. **The default is local transcription and sends nothing. Tell the user before switching to cloud.**

## F3 Timing

```bash
python3 skills/ve-director/doc/scripts/doc_align.py <project>/doc.json
```

Right: exit 0, and `<project>/beats.json` (the start and end of every beat; the authority for all timing from here on) and the subtitle file are written. `worst match` on the last line is information only and has no threshold; when a line really cannot be matched the script stops by itself.
`subtitle not found in the transcript`: the transcriber dropped that line. Listen to that part of `tts/voice.wav`; if it is silent, go back to F2 and redo the line.

Then check the on-screen text against the real timing:

```bash
python3 skills/ve-director/doc/scripts/doc_lint.py <project>/doc.json --beats <project>/beats.json
```

Right: `read_time: ok` and `late_reveal: ok`. These two are reports and do not change the exit code, so read the lines:

- `late_reveal`: a text comes in with under 0.5 s of its beat left, so nobody will see it. Move its `at` to an earlier word of the same narration line. Do not leave it. For a `countdown` it also means the clock is still running (or only just stops) when the beat ends: make `dur` no more than the line prints, or start it earlier.
- `read_time`: a quote card or label is on screen for less than its reading time. Move its `at` earlier, or show the line to the user and let them decide.

`at` is in `doc.json`, so this does not need F2 or F3 again. If you change an `at` after F4, run F4 and F5 again.

## F4 Scenes drawn by code

```bash
python3 skills/ve-director/doc/scripts/doc_code.py <project>/doc.json --render
```

Beats with `source` set to `code` are drawn here (no network needed: the animation library GSAP is installed by `npm ci` and copied next to each page). It first checks that every trigger phrase (`at`) appears in that beat's narration and stops if one does not, so nothing is half drawn. Run `npm ci` once at the repository root before the first use.

Right: one mp4 per beat under `<project>/code_<theme>/`. A trigger phrase that fails: change that beat's `at` in `doc.json` to words the narration really has (change the scene settings, not the narration).

## F5 Cut

```bash
python3 skills/ve-director/doc/scripts/doc_cut.py <project>/doc.json --render
```

Right: `<project>/cut_<theme>/output.mp4` (pictures, narration, burned-in subtitles, loudness set to -14 LUFS) and `cut_<theme>/plan.json` (for optional D).

## F6 Check the film

```bash
python3 tools/nightly/check.py <project>/doc.json <project>/cut_<theme>/output.mp4
```

It measures loudness, peak and length, and lays out frames as `<project>/nightly/sheet.jpg`: for every beat the frame 0.15 s after its first word, and for beats drawn by code a second frame 0.4 s before the beat ends (labelled `tail`), which shows the finished drawing.

It starts with the check every exported film gets (`tools/nightly/film_check.py`; a Concat export runs it by itself): audio and video the same length, the last frame where the file says it ends, no black frames inside the film, loudness and peak, the sound effects really in the mix (when `sfx/sfx_bed.wav` exists), and the film made from the current files. The result is written next to the film as `<film>.check.json` with its SHA-256; the release checklist uploads only that file.

Right: exit code 0. **A film whose check does not exit 0 is not delivered and not uploaded**; fix what it prints. Two lines are reminders and never fail the film: `quiet` (the quietest 5% of the sound is louder than -28 dB, so the music may be covering the voice between lines) and `first30` (the longest stretch without a new picture in the first 30 s, the cover beat left out; over 5 s is worth a look). The stalled-picture and empty-card lists are listed only and do not fail the check; the note that the pace check is off is information too (it only runs for films whose `doc.json` has `pace`). A line starting with `!` (a code-drawn beat that opens on a blank frame for a second or more) does not fail the check either, but fix it: bring the beat's first element in at its first words or at a number like `0.3`.
Then open `sheet.jpg` and look at every cell: the first frame has to match that beat's subtitle, and the `tail` frame has to show the whole chart or list with the right numbers. If you cannot make a cell out, say you did not see it; do not count it as passed.

## Web platforms and logins

Read this before Optional A or B, and before driving any other website with a script.

- A script that drives a website runs its own browser with its own profile. The user being logged in to that site in their everyday browser does not help; the login has to happen once in the window the script opens.
- So the first time on a machine, in a fresh copy of the repository when the profile lives inside it, and whenever the login has expired: open a visible window, tell the user a browser window is coming up and what to log in to, and wait. Never type an account name or a password.
- A script that cannot show a window must stop at once with the command that opens one; it must not sit on a login page nobody can see. If you write a script for another site, give it the same two things: a login-only mode with a visible window, and a check that stops early when there is no login.

| | Where the login is kept | Window | First login |
|---|---|---|---|
| VideoExpress | `tools/ve-runner/.profile` inside the repository (not in git, so a fresh copy has none) | none by default | `S2F_VE_HEADED=1 python3 tools/ve-runner/ve_runner.py --login` |
| TalkingPhotos | outside the repository (`S2F_TP_PROFILE`, default `~/.config/script2film/tp-profile`; a profile already made at an earlier version's default location keeps being used), shared by every copy | always | `python3 tools/tp/tp_browser.py serve` in the background, the user logs in there; the window closes itself after 10 idle minutes |
| MiniMax H3 (Colab) | `~/.config/colab-cli/token.json` (Google account with Google AI Pro) | none | the upstream `scripts/colab_login.py url`: give the user the link, they sign in and paste the code back (`tools/h3/README.md`) |

`python3 tools/doctor/doctor.py` shows both as optional items ("VE login", "TP profile folder").

## Optional A: generated shots (VideoExpress)

`examples/brewing` has one such shot, with the finished clip in `premade/` (its README shows how to use it without an account). The commands below are the author's usual flow and need a VideoExpress account.

```bash
python3 skills/ve-director/doc/scripts/doc_runsheet.py <project>/doc.json --estimate
```

Beats with `source` set to `ve` are written into a run sheet, and the script prints the `tools/ve-runner/ve_runner.py` command to run next. `--estimate` guesses each beat's length from the character count (Chinese only; for an English film wait for F3 and run it without `--estimate`).

- **Ask the user before sending**: every shot spends generation credits on their account.
- The user logs in; do not type account names or passwords for them. VideoExpress runs without a window by default, and its login lives in `tools/ve-runner/.profile`, which is not in git. So the first time on a machine or in a fresh copy of the repository, and again whenever the login has expired, open a window once: `S2F_VE_HEADED=1 python3 tools/ve-runner/ve_runner.py --login`. Tell the user a Chrome window is coming up and wait for them to log in there (the script waits up to 10 minutes, then closes). Logging in to their everyday Chrome does not help: the scripts use their own Chrome profile. Without a login the runner stops at once and prints this command.
- Run `ve_runner.py` in the background with its output in a file (`python3 -u … > <log> 2>&1 &`) and read the end of the file now and then: a command that times out kills the run. The last line `all N shot(s) submitted` is followed by the `ve_collect.py` command to use. A 5-second shot was ready about 2 minutes after it was submitted (measured 2026-11-16, twice); `ve_collect.py` waits for it.
- Do not send a real person's photo to a video model.
- Afterwards: `python3 tools/ve-runner/ve_collect.py --submitted <run>/submitted.json --out <project>/ve_<look>`, then `python3 tools/ve-runner/ve_clipcheck.py <project>/ve_<look> --run <run> --strips`. `<look>` is the name `doc_runsheet.py` printed. Look at the first and last frame of every shot: garbled text, modern objects or the wrong period mean rewording and drawing again, three times at most.

### Using another platform for the shots

Nothing here is tied to VideoExpress: the cut only needs clips in the right folder with the right names.

- Which shots and how long: the beats in `<project>/beats.json` whose `source` is `ve`, in order, are shot 1, 2, 3…; each one's `gen_seconds` is the length to generate (the beat's length rounded up, at least 3 s; `doc_align.py` stops on a beat over 10 s, so split it first). What each shot shows is in the run sheet `<project>/storyboard_<look>.md` that `doc_runsheet.py` writes. Before F3 there is no `beats.json` yet: `doc_runsheet.py --estimate` writes the same list with guessed lengths to `<project>/beats_est.json` (Chinese scripts only).
- Where they go: `<project>/ve_<look>/shotK.mp4`, K counting from 1 in that order. `<look>` is `ve_look` in `doc.json`; without it, `flat` for the `lecture-*` palettes and the palette's name for the others.
- A clip shorter than its beat is slowed down (by at most `max_stretch` in `doc.json`, default 1.2, never more than 1.5) and then held on its last frame.
- Then run `ve_clipcheck.py <project>/ve_<look> --strips` (without `--run`) and go on to F5.
- The rules above still apply on any platform: ask the user before spending their credits, the user logs in, no real person's photo into a video model.

### Google Flow (shots)

`skills/google-flow/SKILL.md`. One clip at a time from Omni or Veo in the user's own Google AI subscription, in the user's own Chrome (Claude in Chrome; Google refuses sign-in in automation-launched browsers). `flow_ingest.py --latest video --to <project>/ve_<look>/shotK.mp4 …` puts it in place with a provenance record; then `ve_clipcheck.py` as above. Tell the user the credits shown on the settings chip before sending.

### MiniMax H3 on Colab (shots)

`tools/h3/README.md`. Generates on the user's own Colab GPU (Google AI Pro); the clips land in `ve_<look>/shotK.mp4` like the VideoExpress ones.

- **Licence first**: the H3 open weights do not cover the United States, the European Union, the United Kingdom or South Korea. The start checklist asks `h3-territory` once the episode has `h3/manifest.json`, and `h3_film.py run` releases the GPU at once when the Colab machine is outside the territory.
- `python3 tools/h3/h3_film.py plan <project>/doc.json --shots` writes one job per VE beat with a **draft** prompt from `doc.json` `shots`. Rewrite each one into 350-500 English words (the upstream `references/prompt-guide.md`; short prompts make H3 burn subtitles) and delete `"draft"`; `run` refuses drafts and prompts under 300 words.
- **Ask the user before sending**, with the spec (number of clips, seconds, resolution) and the cost in compute units; then `python3 tools/h3/h3_film.py run <project>/doc.json --confirmed`, then `python3 tools/h3/h3_film.py collect <project>/doc.json` and `ve_clipcheck.py <project>/ve_<look> --strips`.

## Optional B: host (TalkingPhoto)

`examples/brewing` has a host, with the finished take in `premade/` (its README shows how to use it without an account). The commands below are the author's usual flow and need a TalkingPhotos account; details in `tools/tp/README.md`.

### The look image

The host is made from one still picture, the look image. Settle it before anything is sent.

- A photo the user hands you is reference material, not the look image, unless the user says "use this one as it is".
- The look image: a medium shot from head to waist (`cinematic medium shot framed from head to waist`), the same aspect ratio as `TP_ASPECT` (16:9 unless set), a clean background, the face near the middle. A close-up, a selfie angle or an arm across the frame is not a look image.
- Making it: generate a few candidates from the reference photo with an image tool, using the framing above, or ask the user for a picture that already fits. Generating on VideoExpress spends credits: ask first. Only the user's own likeness, or one the user has the right to use.
- **Stop**: show the candidates and let the user pick. Ask this together with "may I spend the credits". Upload only the one they picked:

```bash
python3 tools/tp/tp_upimg.py "<look name>.jpg"
```

It stops when the picture's aspect ratio does not match `TP_ASPECT`; image generators often give a size that is close but not equal (1376×768), and `--fit` then uploads a centre-cropped copy and leaves the file as it is. It prints the name TalkingPhotos shows for the picture: pass that name to `--look` below.

- The voice has to fit the person on screen. If the narration is a designed or borrowed voice and the host is a real person, stop and ask the user which to change: the voice (back to F2 with that person's reference voice, with their consent) or the host.

### The commands

```bash
python3 skills/ve-director/doc/scripts/doc_host.py split <project>/doc.json
python3 tools/tp/tp_host.py <project> --prefix <code> --look "<the look image's name in the TP media library>"
python3 skills/ve-director/doc/scripts/doc_host.py join <project>/doc.json
```

- **Ask the user before sending**: every segment spends credits on their account.
- The user logs in (in the window `tp_browser.py serve` opens); do not type account names or passwords for them. TalkingPhotos always runs with a window; its login is kept outside the repository, so a fresh copy of the repository is already logged in.
- `tp_host.py` waits for the render and downloads it, so run it in the background with its output in a file too (`python3 -u tools/tp/tp_host.py … --timeout 40 > <log> 2>&1 &`) and look at the file about once a minute; the last line is `all done`. A segment of about 22 s took 11 and 13 minutes, one of 26 s between 15 and 23 (measured 2026-11-16).
- The host photo has to be the user, or a likeness the user has the right to use.
- A round frame over other beats (`"pip"`) crops the host video with `"crop": [w, h, x, y]`. With a look image framed as above the face is near the middle; look at one frame of `host/tp_host.mp4` before choosing the numbers.
- When a segment cannot be sent, the error names a screenshot of the page (`<project>/host/tp_upload/fail_<name>.png`): look at it before trying again.

### Using another platform for the host

- `doc_host.py split` writes the narration in parts, `<project>/host/parts/partK.mp3`, and `host/parts.json` (where each part sits in the narration).
- Make a talking-head video of each part with any lip-sync tool and save it beside the audio as `<project>/host/parts/partK.mp4`. It should be as long as its mp3: `join` scales and pads it to 1920×1080, cuts it to the part's length, and holds the last frame when it is shorter.
- `doc_host.py join` works as before.
- The portrait is whatever that tool takes; it has to be the user, or a likeness the user has the right to use. Ask the user before spending their credits there too.

### MiniMax H3 on Colab (host)

`tools/h3/README.md`. H3 locks the narration audio into the clip: the lips follow the recording and the sound is the narration itself. The person comes from the look image (the same rules as above: the user picks it, it has to be the user or a likeness the user has the right to use), and the prompt can make them gesture, walk along a counter or film a handheld selfie.

- H3 takes at most 15 s per clip: `python3 skills/ve-director/doc/scripts/doc_host.py split <project>/doc.json --max 15 --min 4`.
- `python3 tools/h3/h3_film.py plan <project>/doc.json --host --look <look image> --who "<person, clothes>" [--where "<place>"]` writes one locked job per part with the lines at their times; it can be sent as it is.
- Same licence check and the same **ask before sending** as the shots; then `run --confirmed`, `collect` (it writes `host/parts/partK.mp4`) and `doc_host.py join` as above.

## Optional C: music and sound effects

Not checked with the example film. The music is composed by a program and needs no network; installation and the sound font are in `tools/score/README.md`.

```bash
(cd tools/score && uv run python adapters/doc_arc.py <absolute path of the project>/doc.json --render --out <absolute path of the project>/score_bgm.wav)
python3 skills/ve-director/doc/scripts/doc_sfx.py <project>/doc.json --report
```

The first needs `bgm.arc` in `doc.json`; afterwards point `bgm.src` at `score_bgm.wav`. The second needs `"sfx_on": true` and runs before F5. Someone else's music needs a licence; put the credit in `bgm.credit`.

### Google Flow Music (a song or an instrumental)

`skills/google-flow/references/flow-music.md`. Lyrics and a Sound line in Flow Music's Compose panel, in the user's own Chrome (Google AI Pro includes the Plus plan). `flow_ingest.py --latest music --to <project>/flow_bgm.wav --doc <project>/doc.json …` sets `bgm.src` and `bgm.credit`. The lyrics must be the user's own; label the film as AI-generated (`--synthetic`).

### MiniMax Music 3 on Colab (a song or an instrumental)

`tools/music3/README.md`. On the user's own Colab (Google AI Pro): `music3_film.py plan <project> --caption-file … [--lyrics-file …] [--seconds N]`, `run <project> --confirmed`, `collect <project>` (sets `bgm.src` and `bgm.credit`), or the notebook in the README. No territory limit. The lyrics must be the user's own, and a published film is labelled as AI-generated (`--synthetic`). Measured on an L4: a 60 s song takes about 5 minutes. **Ask the user before booting a GPU** if you run it for them.

## Optional D: final film in Concat

Not checked with the example film. Needs Concat. The `output.mp4` from F5 is already a deliverable film; this step adds the overlay layers: host in a side frame, keyword pills, chapter labels, film grain, photo credits.

```bash
python3 tools/concat/plan2concat_mcp.py <project>/cut_<theme>/plan.json <project> concat_final --font <family>=<font file.ttf> --export <project>/<film name>.mp4
```

Add `--layers <project>/cut_<theme>/layers.json` when `doc.json` has `side`, `pills`, `chapters`, `punch` or `grain`, and `--photo-credits <project>` when it uses photos from `assets/`. The bundled fonts are in `assets/fonts/`. Run F6 again on the new film.

## Optional E: start and release checklists

Not checked with the example film. Described in `tools/checklist/README.md`.

```bash
python3 tools/checklist/checklist.py run <project> --stage start
python3 tools/checklist/checklist.py questions <project> --stage start
python3 tools/checklist/checklist.py answer <project> <id> "<answer>"
```

The programs that send to VideoExpress, send to TalkingPhotos and upload run the checklist themselves at the start and stop when it fails. Answer the questions truthfully; ask the user when you do not know. When it stops you, supply what it asks for. Running anyway needs `--skip-checklist "<reason>"`, which is logged, and needs the user's agreement.

## Optional F: upload to YouTube

Not checked with the example film. Installation and authorisation are in `tools/youtube/README.md` (the user does the authorisation step in the browser). The commands use the virtual environment that README sets up.

```bash
tools/youtube/.venv/bin/python tools/youtube/yt_upload.py whoami
tools/youtube/.venv/bin/python tools/youtube/yt_upload.py upload <film.mp4> --title "<title>" --desc-file <description.txt> --synthetic
```

- **Upload, make public, schedule or delete only when the user says so.**
- Run `whoami` first and read the channel name back to the user.
- The default upload is unlisted; `--publish-at <ISO time>` makes it private and schedules it.
- A synthetic or cloned voice, or generated pictures: add `--synthetic` (YouTube's altered or synthetic content label).
- Do not upload a film that failed F6.
- Record every asset's source and licence in `<project>/assets/CREDITS.md`; put required credits (CC BY and so on) in the video description. Do not use news-agency or broadcaster photos or footage.


## Optional G: theme preview

Three themes playing three of this film's own code beats side by side, before anything is voiced, so the theme can be picked while the script is read. Pick before optional A: the generated shots carry the theme's colours.

```bash
python3 skills/ve-director/doc/scripts/doc_theme_preview.py <project>/doc.json                 # about 45 s
python3 skills/ve-director/doc/scripts/doc_theme_preview.py <project>/doc.json --pick <theme> "<why>"
```

- Writes `<project>/preview/theme_preview.mp4` (a 2x2 grid with no sound: three themes and a cell naming them and why each was offered) and `theme_preview.jpg` (every beat's last frame, one row per theme). Show both with the script.
- The motion is real, the pace is estimated from the script (5 characters a second); pictures the generated shots have not made yet show as grey placeholders.
- Which three: the previous episode's (or the series default's) theme, one with the other brightness, one with another shape; `series.json` `"themes"` lists the candidates in order; `--themes a,b,c` and `--beats B3,B7` choose by hand.
- `--pick` writes `"theme"` into `doc.json` and records the reason in `preview/theme_choice.json`. Skipping this step changes nothing.
- `doc_lint` reports the same theme three episodes in a row (a reminder, not a failure).
