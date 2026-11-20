# ve-runner — VideoExpress run-sheet executor (no LLM in the loop)

Drives app.videoexpress.ai with Playwright from a PromptStudio storyboard / run sheet.
The pipeline drafts, a person approves: every generated image stops at a QC gate
(pick candidate 1/2, `r` re-roll, `s` skip the shot (no video, the run goes on), `q` quit) before it is used.
Create Image waits for a free slot like Create Video (`wait_for_slot`): with five videos processing on the account a
Create Image sat four minutes with no candidate (2026-10-24); a timeout is retried once when a slot frees up.
Live test 2026-10-24: shot7 answered `s` -> "shot7 skipped at QC (no video)", the run went on to shot8 Create Image.

## Setup (once)
- Python 3.13 + `pip install playwright` (uses the system Chrome via `channel="chrome"`, no browser download)
- First run pops a Chrome window with its own profile (`.profile/`, gitignored: it holds the VE login). Log in there yourself; the login persists.
- Chrome refuses automation of your everyday profile (Chrome 136+), hence the separate profile. One runner/collector at a time per profile.

## Run
```
python3 ve_runner.py x.md                                  # masters for the cast + all shots
python3 ve_runner.py x.md --shots 1 3                      # only these shots
python3 ve_runner.py x.md --masters runs/<ts>/masters.json # reuse masters from an earlier run
python3 ve_runner.py x.md --run-dir <projects>/<film>/ve-runs  # runs/<ts>/ in the film's folder (first stdout line: run dir)
python3 ve_runner.py --inspect                             # dump modal DOM only
S2F_VE_HEADED=1 python3 ve_runner.py --login               # first time on a machine or a fresh copy: open a window, the user logs in, it closes
                                                           # (without a login the default headless run stops at once and prints this command)
python3 ve_runner.py x.md --step                           # confirm before every click
python3 ve_runner.py x.md --takes 3                         # 3 videos per shot from the same first frame, to pick one
python3 ve_runner.py x.md --auto-pick                      # accept candidate 1 at every image QC gate (official VOX: first take ships)
python3 ve_collect.py --submitted runs/<ts>/submitted.json --out DIR   # download finished clips
python3 ve_voice.py --submitted runs/<ts>/submitted.json --labels shot21_t2 --ref voice.wav --out DIR [--run-dir …/ve-runs]  # re-voice clips (Voice Changer)
python3 -m pytest -q                                       # run-sheet parser + ve_qc log-state tests
```
QC answers: interactive prompt, or without a TTY use `ve_qc.py` (it writes `runs/<ts>/decision.txt`):
```
python3 ve_qc.py runs/<ts>        # wait for the next QC gate; prints the label and runs/<ts>/<label>_compare.jpg (candidates side by side)
python3 ve_qc.py runs/<ts> 2      # answer 1/2/r/q, then wait for the next gate or the end (exit 0 = at a gate, 2 = finished, 1 = failed)
```
Artifacts in `runs/<ts>/`: `masterN.jpg`, `masters.json` (actor → My AI Images id), candidate jpgs,
`shotN_frame.jpg`, `submitted.json` (label → video uuid; `shotN_tK` with `--takes`), screenshots, `run.log`.
Watch `run.log`, not stdout: stdout redirected to a file is block-buffered unless run with `python3 -u`.

Chrome runs without a window by default (2026-11-12; `ve_runner.py`, and `ve_voice.py` / `ve_frames.py` through `launch_browser`). `S2F_VE_HEADED=1 python3 ve_runner.py …` (the old name `VE_HEADED` also works) opens a window: use it to log in by hand when the session has expired (headless stops after 90 s with that hint). Tested headless: two 9:16 image-to-video shots, QC gates and submit. Not yet tested headless: `ve_voice.py`, `ve_frames.py`, reference-image upload, Consistent Character. Memory is about the same either way: peak 839 MB headless against 875 MB headed, 7 processes.

## Run sheet
- `# Actor Portrait…` section: `Actor N: <prompt>` = the master (character reference) prompt: one actor, full body, plain background.
  A sheet without actor lines is fine when no shot casts anyone (all `Cast: none`, e.g. doc-mode collage shots with `--no-cc`).
- `## Shot N` bullets: `Duration`, `Text-To-Image Prompt`, `Image-To-Video Prompt`, optional
  `Cast: Actor 2, Actor 1` (slot order; default = actors named in the image prompt; `none` = no reference) and
  `Start: master | chain | same` (`chain` = continue from the previous shot's last frame, see below; `same` = animate the
  previous shot's first frame again with this shot's video prompt, no new image: an A/B prompt test on one frame).
  Optional `Save: master`: the picked first frame is saved in My AI Images (`runs/<ts>/saved.json`, label → id) and no video
  is submitted; pass that id in a later `--masters` file. Used to draw a turnaround sheet from an existing master (Cast set).
  Optional `Narration: <audio file>` (path relative to the sheet, ≤ 10 s, checked with ffprobe before the browser opens): the
  shot goes through VE's Narration Video path with that audio, see 10. Not with a spoken line, not with `Save: master`.

## What it does
1. Opens Create Video From Prompt **once** and keeps it open: reopening resets every option and both reference slots.
2. Masters: for each cast actor without one, Create Image (CC off) → QC → **Save Image** → finds the My AI Images item
   (name = first ~60 chars of the prompt, created after the click; candidates are not auto-saved and the library re-encodes them).
3. Per shot: Reference Photo 1/2 ← the cast masters via Select Image → My AI Images → `.library-item[data-ident=<id>]` → Choose;
   slots are verified before every Create Image and re-picked only when empty or mismatched. CC on with an empty slot makes VE refuse
   ("Please select a reference photo.") — the runner raises on such alerts instead of waiting.
4. Create Image → QC → duration → Video Only ON, enhance OFF → Create Video. The footer `Video: <uuid>` must change and the
   uuid must appear in My AI Videos (jobs over the 5-in-flight cap are dropped silently, with no record); the runner waits for a slot.
   With `--takes N` it submits N videos from the same selected frame.
   Candidate detection remembers every candidate already returned (by src and by content hash): the candidate carousel hides
   older sets and shows them again, which once made a shot return an earlier shot's candidates after about six Create Images.
5. `ve_collect.py` matches clips by uuid and downloads them via `library/download/<id>`.
6. `Start: chain`: the runner waits until the previous shot's videos are completed; with several takes it downloads them,
   takes each last frame and opens a QC gate `shotN_chain` showing those last frames side by side to pick the take to continue.
   Then the chosen clip's menu > **Save Last Frame** (Title `#modalFieldName` = `chain_<run>_shotN`, Save) puts VE's own last
   frame in My AI Images, the dialog is reopened (closing it resets options and slots), and that image becomes the frame to
   animate via Use from Library. No image is generated, so Consistent Character is off for that shot. A chain shot cannot be
   submitted in parallel with the shot before it; the first shot of a run cannot be a chain shot.
   Live tests: 2026-10-09 with download → ffmpeg → upload (PSNR 41 dB to the chosen last frame; 13.7 dB to the other take);
   2026-10-10 with Save Last Frame (37.4 dB to the chosen take's last frame; 12.7 dB to the other take, both new takes).
7. Lipsync (a shot whose video prompt has `says in …: "line"`): ticking Lipsync HD disables the main video prompt and
   turns Create Video into `button-generate-talking-video`, which opens "Create Lipsync Audio". Its Video Prompt reuses
   `id="opt_prompt"` (found by its "Actor 1 is…" placeholder) and takes the shot's video prompt; Actor 1 Script
   (`#opt_prompt_actor1`) takes the line; then Create. Live test 2026-10-09: clip with speech audio, mouth moving;
   the clip came out 4.0 s for a 5 s shot (the length seems to follow the speech).
   Two spoken lines (one by Actor 1, one by Actor 2; each line's speaker is the last `Actor N` named before it): the runner
   clicks Add Actor 2 and fills Actor 2 Script (`#opt_prompt_actor2`). With one line, a leftover Actor 2 Script is cleared.
   Live test 2026-10-10 (a short line from Actor 2, then one from Actor 1): both takes spoke the lines in the written order, male voice
   then female voice (pitch about 130-155 Hz, then 250-320 Hz). Swapped (Actor 1 first): again the written order, so the
   prompt sets who speaks first, not the script slot.
8. `ve_voice.py` (Voice Changer): uploads a reference voice to Media Library > Audio (or reuses `--ref-id`), right-clicks
   each clip in My AI Videos > Voice Changer > Choose Sample Audio > Apply, and downloads the new video. Frames and length
   stay identical to the source (tested 2026-10-09); only the voice changes. It swaps the voice of the whole clip, so it
   does not suit a two-speaker clip.
9. A crash or an early exit is written to `run.log` (`crashed:` + traceback, or `stopped: …`), so `ve_qc.py` reports it.

10. Narration (`Narration:` bullet): every shot's audio is uploaded to Media Library > Audio before the dialog opens
   (`runs/<ts>/narration.json`, path → library id). Per shot: Lipsync HD off, **Narration Video** on, Advanced Mode off (no
   duration is set: the clip length follows the audio), video prompt filled. With Narration Video ticked the visible Create
   Video is `button-generate-talking-video` (the same class as lipsync); it opens "Create Narration Video - Create Audio" with
   tabs Text to Speech (Microsoft voices, `#tts_text_lang` lists Chinese (Taiwanese Mandarin, Traditional)) / CloneVoice.ai /
   Voice Recording / Import Audio. The tabs switch only on a real mouse click (a DOM `click()` leaves the first pane). Import
   Audio > `button.button-select-file` opens the Media Library picker (Audio folder > item > Choose); the tab states a 10 s cap.
   Then **Create Narration Video**. The clip lands in My AI Videos like any other. If the library check still fails, the
   uuid is kept as unconfirmed instead of resubmitting. The 120-character text box belongs to the TTS / CloneVoice tabs, unused here.
   Live test 2026-10-18 (5.15 s Chinese narration, paper-collage door, 6 s plan): clip 6.04 s at 1920x1080/24 fps, our audio
   placed verbatim from 0 s (envelope correlation 1.00), voice ends at 5.10 s, nothing cut. The door swung shut although the
   prompt said it stays still. VE's library API keeps only the first ~60 characters of the video prompt (`name`), so whether
   `[ACTION a-bs]` tags survive on this path is not verified.
   Host trial 2026-11-16 (a talking host instead of TalkingPhotos: one look image with `Start: image`, a 25.7 s Chinese
   narration cut between lines into four parts of 9.42 / 5.57 / 5.37 / 5.35 s, two rounds of four clips): all four clips
   of a round were ready about two minutes after the last submit; the audio sits verbatim from 0 s; every clip begins and
   ends close to the look image, so the parts join without a visible jump; face and background did not drift. Against
   that: the fourth clip of both rounds carries burned-in gibberish captions for most of its length (round 1 with the
   eight-tag prompt: English-looking text that garbles the tag names; round 2 with a plain-sentence prompt that says "no
   subtitles": Chinese-looking text), hands came into frame briefly in two clips of each round although the prompt said
   they stay out, and the user judged the Chinese lip sync less accurate than TalkingPhotos. A third round the same day
   (two English lines of 2.9 and 8.1 s, three short Chinese lines of 1.4 to 2.2 s, plain-sentence prompt): no captions
   in any of the five, hands in two; the user watched it with our narration alone and found the mouth out of step with
   the speech in English and in Chinese alike. The clips' own sound is not our narration alone: subtracting the supplied
   audio (aligned at 0 ms) leaves 12 to 33 % of the energy in three clips measured, and there is sound after the
   narration ends. So take the picture only and lay the narration yourself. The likely reason for the loose lip sync is
   that the mouth follows what VE generates rather than the imported audio; this was not tested further. The earlier
   short vlog that lip-synced well did not use this path: its lines were spoken from the prompt (`--speech-in-prompt`)
   and re-voiced with Voice Changer. A lower-left circle (crop 680x680 at 620,20) cuts the caption area away; a
   700-px-wide full-height right frame does not. Conclusion: Narration Video is not a way to lip-sync a host to a
   given narration; TalkingPhotos stays the host path. `doc_host.py split` cannot make such parts (its cap is at least
   20 s); the parts were cut by hand.
   Two runner faults showed up and were fixed in that trial: `close_modal` clicked a Close button that did not close the
   dialog, and a picture uploaded after narration audio in the same run landed in the Audio folder (the upload dialog
   keeps the folder of the page's first upload; `upload_file` now loads the page again when the folder changes).

## Known gaps
- `Start: image <file>` (2026-10-22): a frame made outside VE (a candidate retouched by hand: a nail wound VE would not draw
  in three text re-rolls) is uploaded to Media Library > Images (`upload_file`; the name must contain the file stem) and
  animated via Use from Library, the same two steps the chain shot uses. No image is generated, no Cast. Live test: the
  painted wound stayed visible through the whole 5 s clip.
- First Frame / Last Frame card (a chosen last frame as well as the first) is not used yet.
- Lipsync takes one line per actor; a back-and-forth longer than one line each needs more shots.
- The footer "Consistent Character" button (`button-consistent-character-auto`) puts the selected candidate into slot 1; the official
  workflows avoid it and so does the runner.


Start checklist: when the run sheet sits inside an episode folder (one with `doc.json` or `day.json`, searched upwards),
`ve_runner.py` runs `tools/checklist` (start stage) before submitting anything and stops if an item fails;
`--skip-checklist "<reason>"` runs anyway and logs a line in `<episode>/nightly/checklist_skips.jsonl`.
A run sheet outside any episode folder (a story film) is not checked.
