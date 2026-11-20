# Installing Script2Film

From an empty machine to the first film. Everything here was run on 2026-11-17 on a MacBook Pro (M3 Max), with an empty
home folder and a fresh clone, and the times are the ones measured then. Apple Silicon macOS is the only system this has
been run on.

Allow about 30 minutes and about 7 GB of downloads the first time. Nothing here needs an account or an API key.

## What you need first

[Homebrew](https://brew.sh), then:

```bash
brew install git ffmpeg node python python@3.11
```

`python` runs the project's own scripts; `python@3.11` is the version the two speech environments were tested with.

## Steps

Run everything from the project folder.

| # | Command | What it does | Measured |
|---|---|---|---|
| 1 | `git clone <this repository> && cd <folder>` | gets the project | seconds |
| 2 | `python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt` | the project's Python packages, in its own environment | under a minute |
| 3 | `.venv/bin/python -m playwright install --only-shell chromium` | Playwright's own headless browser (about 97 MB, with the small ffmpeg it records screens with), which reads the built scene pages: sound marks, screen-recording beats and the tests | about 15 seconds |
| 4 | `npm ci` | HyperFrames and GSAP, which draw and render the scenes | under a minute |
| 5 | `npx hyperframes browser ensure` | the headless browser that renders the scenes | under a minute |
| 6 | the two `curl` lines below | the two fonts (OFL 1.1, about 29 MB) | about 2 minutes |
| 7 | `bash tools/doctor/setup_voice.sh` | the narration and transcription environments and the voice model (about 6 GB) | 20 to 25 minutes |
| 8 | `python3 tools/doctor/doctor.py` | checks all of the above | seconds |

```bash
curl -L -o assets/fonts/NotoSansTC-Variable.ttf 'https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf'
curl -L -o assets/fonts/NotoSerifTC-Variable.ttf 'https://github.com/google/fonts/raw/main/ofl/notoseriftc/NotoSerifTC%5Bwght%5D.ttf'
```

The sound effects come with the clone (`assets/sfx/`, about 21 MB); nothing to download for them. See `assets/README.md`
for adding your own.

Step 8 should end with `✓ ready to go` and exit code 0. Each `✗` line is followed by a `→` line with the fix. You can also
skip straight to step 8 after cloning and follow its `→` lines one at a time: they are the same commands.

Then make the first film: `examples/coffee/README.md`, or tell your agent to make `examples/coffee` following the
documents. Measured on the same clean setup: 3 minutes 17 seconds for the voice, 1 minute 21 seconds to pick the takes
(this includes the one-time download of the transcription model, about 1.5 GB), and 1 minute 28 seconds for timing,
drawing, cutting and the check together. The film is 24.8 seconds long.

## Things worth knowing

- **Keep typing `python3`.** Homebrew's Python refuses `pip install` outside an environment, so the packages live in
  `.venv`. When a script in this project is started with the system `python3` and `.venv` exists, it restarts itself
  with `.venv`'s Python. You do not need to activate anything. To run the tests, use
  `.venv/bin/python -m pytest <folder> -q`. Set `S2F_NO_VENV=1` to turn the restart off.
- **Step 7 looks stuck and is not.** Installing the Qwen3-TTS packages took 15 minutes and prints nothing for most of
  it. If it fails or you stop it, run the same command again: finished parts are skipped and the model download
  resumes.
- **Where step 7 puts things.** `~/s2f-voice/` by default (`bash tools/doctor/setup_voice.sh <folder>` for another
  place): `qwen3-tts/` (the official code and its environment) and `_models/` (the voice model and the transcription model
  `whisper-cpp/ggml-large-v3-turbo.bin`, about 1.6 GB). The transcription program `whisper-cli` comes from
  `brew install whisper.cpp`, which the script runs if it is missing. The two paths are written to `~/.config/script2film/config.json`. Qwen3-TTS is pinned to the commit
  this project was tested with.
- **Designing a new voice needs one more model.** The examples ship their reference voices. To design your own
  synthetic voice (`tools/tts/design_voices.py`), run `bash tools/doctor/setup_voice.sh --design` for the VoiceDesign
  model, about 4.2 GB more.
- **`sox: command not found` and the `flash-attn` warning** during the voice step come from the voice model's own
  packages and can be ignored.
- **Two headless browsers, on purpose.** Step 3 is Playwright's (in `~/Library/Caches/ms-playwright`, or
  `PLAYWRIGHT_BROWSERS_PATH`), step 5 is the one HyperFrames renders with (in `~/.cache/hyperframes`). Without step 3
  the scene tests and the sound-mark and screen-recording beats stop with "Executable doesn't exist". Sending shots to
  VideoExpress and TalkingPhotos uses your installed Google Chrome instead, not either of these.
- **The optional parts are separate.** Concat, VideoExpress, TalkingPhotos, composed music and YouTube upload each have
  their own setup, described where they are used in `docs/FLOW.md`. `python3 tools/doctor/doctor.py --need concat,ve,tp,youtube`
  checks them.
- **Agents with a sandbox** need three things allowed: network access (installing), the
  voice and transcription folders outside the repository, and connections to 127.0.0.1 (HyperFrames' renderer). What
  each is for and what a blocked one looks like: `docs/FLOW.md` F0.
- **Checking without the voice models.** `python3 tools/doctor/doctor.py --skip voice` reports the voice and
  transcription items as skipped instead of failing, for a machine that only works on the code (this is what CI runs).
  Every other item still has to pass.

## Not covered

Windows, Linux and Intel Macs have not been tried. The tools are ordinary ones (Python, Node, ffmpeg), and the default
transcription (whisper.cpp) builds on other systems too: build `whisper-cli` from <https://github.com/ggml-org/whisper.cpp>,
download `ggml-large-v3-turbo.bin` from <https://huggingface.co/ggerganov/whisper.cpp>, and set `S2F_WHISPER_CPP_MODEL`
(and `S2F_WHISPER_CLI` if it is not on PATH). The cloud transcription in `docs/FLOW.md` is the other way.
