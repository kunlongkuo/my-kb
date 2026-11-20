# Script2Film

Tools that turn a script into a narrated explainer film: cloned or designed voice, word-level timing, scenes drawn by code, subtitles, a cut, and a check. The default path needs no account and no key: voice, transcription and rendering all run on this machine (only `npm ci` and the first model download need a network). Generated footage, a talking host, Concat and YouTube upload are optional.

## Before the voice: the user approves the script

Do not make the voice (F2) until the user has seen the narration and the beat table and said yes to this script.

- Show every narration line and the beat table (for each beat: which lines, which picture), then wait for the user's answer.
- Approval is the user's yes to this script, after reading it. The only other case: before you started, the user said in so many words that they do not need to see the script before the voice is made; then show it to them anyway and go on. "Make me a film", "do it all and report back" and "don't ask me questions" are not approval.
- If the user is not there, stop at F1 with the script saved (`doc.json`, and `facts.md` when there is one) and tell them it is waiting for their OK.
- The program enforces this: `doc_tts.py` makes no voice for a script without approval and exits with code 4. Pass `--script-approved` only after the user has approved this script; passing it for them is reporting an approval that was not given. Change any narration line afterwards and the script needs approval again. The bundled examples, unchanged, count as approved.
- This does not loosen the rules on spending credits, uploading or publishing.

## Map

- `docs/FLOW.md`: the steps, with commands and what to do when one fails. Start here.
- `skills/`: `script2film` (make an explainer film), `ve-director` (VideoExpress storyboards; its `doc/` holds the film scripts and the `doc.json` reference).
- `tools/`: `doctor` (install check), `config`, `tts`, `nightly` (film check), `checklist`, `ve-runner`, `tp`, `h3` (MiniMax H3 shots and host on the user's own Colab GPU; licence limited by territory), `music3` (MiniMax Music 3 songs and instrumentals on the user's own Colab GPU), `concat`, `score`, `youtube`, `agents`, `assemble` (cuts the clips into one picture track and writes `plan.json`; `doc_cut.py` calls it), `drama` (a lip-synced short drama with no narrator), `qa` (frame-by-frame motion check of a film, transcription hallucination guard), `assets` (copy fonts and sounds from an older library, generate sound effects on VideoExpress), `site` (builds the English website pages and the website copy of Prompt Studio), `prompt-studio` (one HTML page that writes VideoExpress prompts).
- `examples/coffee/`: a four-line film to make first.
- `examples/brewing/`: a five-line film with a generated shot and a host; `premade/` holds the generated files (its README has the steps).
- `assets/`: bundled fonts and sound effects.

## Making a film

Use the `script2film` skill. If your agent has no skill mechanism, read `skills/script2film/SKILL.md` directly.

1. Run `python3 tools/doctor/doctor.py` first and fix what it prints. A new machine: `docs/INSTALL.md` (about 30 minutes; ask the user before the long download step).
2. Follow `docs/FLOW.md`.
3. Reply in the language the user writes in. Chinese subtitles and on-screen text are Traditional Chinese; the scripts convert text to Simplified for the voice model themselves.

## Stop and wait for the user

- Before the voice: the user approves the script (the section at the top).
- Ask before sending shots to VideoExpress, TalkingPhotos or MiniMax H3 on Colab, or booting a Colab GPU for MiniMax Music 3: it spends the user's generation credits or compute units.
- Before making a host: a photo from the user is reference material. Prepare look-image candidates, let the user pick one, and check that the voice fits the person on screen (`docs/FLOW.md`, Optional B).
- Upload, publish, schedule or delete a video only when the user says so.
- Tell the user before using cloud transcription (`"asr": "cloud"`): the narration audio is sent to Groq and ElevenLabs. The default is local.

## Do not

- Type account names or passwords for the user. On a login page, stop and ask the user to log in.
- Put keys in code, in `config.json` or in a project folder. They go in `~/.config/script2film/secrets.json` or the environment. Never print a key.
- Send a real person's photo to a video model. Do not use news-agency or broadcaster photos or footage. Record the source and licence of every asset in the project's `assets/CREDITS.md`.
- Deliver or upload a film that fails its film check (`tools/nightly/film_check.py`, run by every Concat export; `tools/nightly/check.py` for explainers). Do not write your own Concat export loop: call `tools/concat/concat_export.export()`.
- Bypass `tools/checklist` when it stops a step. `--skip-checklist "<reason>"` needs the user's agreement, and the skip is logged.

## Changing the code

- Tests: `.venv/bin/python -m pytest -q` from the repository root (or `python3 -m pytest -q` when the packages are in your own Python); it runs the tests under `skills/` and `tools/`. `tools/score` has its own (`cd tools/score && uv run python -m pytest -q`). Many scene tests need the two fonts in `assets/fonts/` (not in git; `tools/doctor/doctor.py` prints where to get them) and a git checkout.
- A script that reads an `S2F_*` setting starts with the four config lines (`tools/config/tests/test_config.py` checks this).
- After adding or renaming a skill under `skills/`, run `python3 tools/agents/sync.py`.
