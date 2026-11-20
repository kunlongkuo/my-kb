# Agent trials

Which AI agents have made a film from this repository using only its documents
(`AGENTS.md`, `skills/script2film/SKILL.md`, `docs/FLOW.md`), and what to watch
for when you try another one.

## What has been run

Tried in November 2026, once or twice each, on one machine (Apple Silicon,
macOS). During the first three runs `examples/coffee` had a Chinese script; it
is in English now, with the same four scenes.

| Agent | Model | Core path, no accounts (`examples/coffee`) | Generated shot + host (VideoExpress, TalkingPhotos) |
|---|---|---|---|
| Claude Code | Claude Opus | works | works |
| Google Antigravity | Gemini 4 Argon, low | works | works |
| opencode + Ollama | Qwen 27b (MLX), local | works, about 13 minutes | works, about 35 minutes; needed help with the first login |
| Claude, as a subagent from a fresh start (below) | Claude Opus | works, about 12 minutes including a second, new film | not tried |
| Google Antigravity, second run (below) | Gemini 4 Hydrogen, medium | works, about 15 minutes including a second, new film | not tried |
| opencode, third run (below) | DeepSeek V4.1 Flash (free tier) | works, about 20 minutes for two films | not tried |

"Works" means the delivery check (`tools/nightly/check.py`) exited 0 and the
film's length fell inside the example's `expected.json` range.

### Claude from a fresh start (2026-11-17)

- **Agent.** Claude (Opus), started as a subagent. It had only the project
  folder and two sentences from the user: no earlier conversation and no
  notes. It was told to read only the project's own files and program output,
  and not to use any paid service, account or key.
- **Project state.** An earlier state of the repository, before the program messages
  were changed to English: the install check, the delivery check and the other
  programs still printed Chinese. The machine already had the voice and
  transcription environments and the config file from an earlier install; the
  fresh copy had no `node_modules` and no fonts.
- **Request 1: make `examples/coffee`.** Result:
  `examples/coffee/cut_lecture-finance/output.mp4`, 24.80 seconds; the delivery
  check exited 0.
- **Request 2: a new 25 to 35 second English explainer, "Why does bread go
  stale?", with code-drawn scenes only.** Result: five narration lines and five
  beats (`compare`, `formula`, `list_reveal`, `compare`, `formula`), palette
  `lecture-food`, with the synthetic voice that ships with `examples/coffee`;
  30.30 seconds; the delivery check exited 0. The first render listed all five
  beats as sparse cards; after adding `"big": true`, three were listed (listed,
  not blocking).
- **Time.** About 12 minutes in all. The voice took longest, about 2.5 minutes
  per film. It changed no code and met no program errors.
- **Along the way.** The install check first listed three items (HyperFrames,
  GSAP, fonts). The agent ran the commands it printed, `npm ci` and the two font
  downloads, and the check then passed.
- **The user was not there.** The agent wrote down the questions it would have
  asked and carried on. Under the documents as they are now, it should have
  stopped at F1 with the script saved (`docs/FLOW.md` F1); since 1.0.0,
  `doc_tts.py` stops there by itself.

The documentation problems it reported, all fixed in later commits:

| It reported | Now |
|---|---|
| The programs printed Chinese; it had to translate their output to go on | They print English |
| `skills/ve-director/doc/README.md` said the finished film is exported from Concat, which contradicted `docs/FLOW.md` | Made consistent: `cut_<theme>/output.mp4` is the film, Concat is optional |
| The same README did not list the `lecture-*` palettes for `theme` | Listed, all ten themes |
| The `facts.md` format was explained only in Chinese | Explained in English, and English column names are accepted |
| No document mentioned the install-scripts warning from `npm ci` | Explained in `docs/FLOW.md` F0 |
| Nothing said what to do at F1 (show the script, wait for approval) when the user is away | Stop at F1 with the script saved. Since 1.0.0, `doc_tts.py` makes no voice without the user's approval (`--script-approved`), and `AGENTS.md` says what counts as approval |
| Nothing said whether the example's synthetic voice may be reused when the user names no voice | It may (`docs/FLOW.md` F1) |

### Google Antigravity, second run (2026-11-17)

- **Agent.** Google Antigravity, model Gemini 4 Hydrogen (medium), working from
  the documents as they were after the program messages changed to English.
- **Project state.** An earlier state of the repository. A fresh copy with no
  `node_modules` and no fonts; the machine already had the voice and
  transcription environments.
- **Requests.** The same two as the Claude run above: make `examples/coffee`,
  then a new 25 to 35 second English explainer, "Why do onions make you cry?",
  with code-drawn scenes only, in `examples/onion`.
- **Results.** `examples/coffee`: 24.80 seconds; the delivery check exited 0.
  `examples/onion`: four beats (`formula`, `flow`, `compare`, `list_reveal`),
  palette `lecture-food`, 25.60 seconds; the delivery check exited 0.
- **Time.** About 15 minutes for both films.
- **Along the way.** The install check listed HyperFrames, GSAP and the two
  fonts as missing; the agent ran the commands it printed and the check passed.
  The agent's sandbox blocked three kinds of action (below); once they were
  allowed, the runs finished. The first cut of the onion film was 24.4 seconds,
  a little short; the agent raised `gaps.default` from 0.6 to 1.0 and re-ran
  the timing, which gave 25.60 seconds. Looking at the check sheet, it found
  two picture problems itself (A and B below) and worked around them in its
  `doc.json`. It changed no code.
- **It did not stop at F1.** It went on without showing the user the script
  and the beat table. Asked afterwards, it said it had read that rule and
  skipped it. It is the second agent to skip F1 when asked to do everything and
  report at the end; the first was the Claude subagent above, on the same day,
  when the documents did not yet say what to do while the user is away. Since
  1.0.0 the program holds this stop: `doc_tts.py` makes no voice for
  a script the user has not approved (exit code 4), and `AGENTS.md` says at the
  top what counts as approval.

What it reported, and what was done:

| It reported | Now |
|---|---|
| A. `flow` with `"look": "pipe"` on a light palette (`lecture-food`): the labels of the first two nodes were light text on the cream ground and hard to read. It switched to `"look": "web"` | Fixed: on a light palette the `pipe` and `streams` tiles stay dark and the text around them takes the palette's text colours (a reached `hot` node's label red); the scene table says so |
| B. `list_reveal` with `"big": true`: an item long enough to wrap had its second line covered by the next item. It shortened all three items to one line | Fixed: a wrapped item pushes the items below it down, and a list that would reach the subtitle band gets smaller words until it fits. The scene table gives the measured one-line lengths (about 33 English or 16 Chinese characters with `big`) |
| C. Its sandbox blocked downloading the fonts, reading the voice and transcription environments outside the workspace (their `pyvenv.cfg`), and HyperFrames' headless browser connecting to 127.0.0.1 (`connect EPERM`) | Documented: `docs/FLOW.md` F0 lists the three permissions the project needs and what each blocked one looks like |

### opencode with DeepSeek, third run (2026-11-17)

- **Agent.** opencode, model DeepSeek V4.1 Flash on its free tier.
- **Project state.** The documents and programs of 2026-11-17, with the
  approval stop in `doc_tts.py` in place.
- **Results.** Two films, one of them a new explainer about yawning, in about
  20 minutes. Both passed the delivery check.
- **It stopped at F1** and asked the user before the voice was made.
- **Along the way.** The install check listed HyperFrames, GSAP and the two
  fonts as missing; the agent ran the commands it printed and the check passed.
  Voice, timing, drawing and cutting met no errors. It changed no code.
- **The hard part: the check passed, the picture was wrong.** The first render
  of the yawning film exited 0, but `nightly/sheet.jpg` showed the first beat
  opening on a blank frame, a `countdown` clock cut off by the end of its beat,
  and three `relation` cards drawn on top of one another. The agent found this
  by looking at the sheet, changed only `at`, `dur` and `rows` in its
  `doc.json`, and ran F4 to F6 again.

What it reported, and what was done:

| It reported | Now |
|---|---|
| A `countdown` clock can run past the end of its beat, and `late_reveal` says nothing | `doc_lint.py --beats` reports it under `late_reveal`, with the largest `dur` that fits |
| `relation` with `rows`: three long English labels in one row overlap, and no document warns | A row too wide for the even spread is spread by the cards' measured widths; cards that still overlap or run off the frame stop `doc_code.py` with what to change |
| A beat that opens on a blank frame still passes `check.py`; only the sheet shows it | `check.py` prints a `!` line for a code-drawn beat that shows nothing for its first second (listed, not blocking; measured on five films, it lists none of their 130 code-drawn beats) |

## Trying another agent

1. Start the agent in the repository root, so it finds `AGENTS.md` and the
   skill. If it has no skill mechanism, tell it to read
   `skills/script2film/SKILL.md`.
2. Run `python3 tools/doctor/doctor.py` and fix what it lists.
3. Ask for `examples/coffee`. It needs no accounts.
4. Compare the film's length with `examples/coffee/expected.json` and look at
   `nightly/sheet.jpg`.
5. Only then try `examples/brewing` or your own film.

## Problems you may meet

| Symptom | Cause | What to do |
|---|---|---|
| The VideoExpress step stops at once with a login message, or the agent loops on it | The login lives in a profile folder outside version control; a fresh clone has none, and the program runs without a window by default | Run `S2F_VE_HEADED=1 python3 tools/ve-runner/ve_runner.py --login` yourself, log in, then let the agent retry. Logging in to your everyday browser does not help |
| A TalkingPhotos step stops on a login page | Same, for the TalkingPhotos profile | Log in in the window the program opened, then rerun the same command. The window closes after 10 idle minutes |
| The agent gives up, or reports failure, while a platform is still rendering | Its command timeout is shorter than the wait: a 5 s VideoExpress shot takes about 2 minutes, a 22 s TalkingPhotos host 11 to 13 minutes | Tell it to run those two programs in the background, write output to a file, and check back (`FLOW.md`, Optional A and B) |
| The agent uploads your photo as the host image as it is | It skipped the look-image step | Point it to "look image" in `FLOW.md` Optional B: your photo is reference material, it shows you candidates, you pick. `tp_upimg.py` stops on a wrong aspect ratio; `--fit` crops |
| The face on screen and the voice are different people | Host added to a film that already had a narrator voice | The voice must fit the person on screen (`FLOW.md` Optional B) |
| A line of text flashes at the very end of a beat, and the agent says the film is fine | It did not run the timing report after F3 | `python3 skills/ve-director/doc/scripts/doc_lint.py <project>/doc.json --beats <project>/beats.json`, then hang the `at` on an earlier word |
| Downloads fail, the voice step cannot read `pyvenv.cfg`, or the render stops with `connect EPERM 127.0.0.1` | The agent's sandbox blocks network access, folders outside the workspace, or local connections | Allow the three things listed in `docs/FLOW.md` F0 for this workspace, then rerun the step |
| `doc_tts.py` stops with exit code 4, or the agent asks to pass `--script-approved` for you | The narration has not been approved: the agent did not show you the script and the beat table at F1, or it changed a line afterwards | Read the narration and the beat table it shows you. Say yes only to the script you have read; the agent then reruns with `--script-approved` (`AGENTS.md`, top section) |
| The agent treats a `⚠` line, or `sox: command not found`, as an error | Reminders, not failures | Only a non-zero exit code stops the flow. Lines ending in "(a reminder, not a failure)" are advice |
| Quoted scripture goes unchecked | No program here reads a full Bible text; quotes are only compared with the excerpts typed into `facts.md` | Have the agent show you every quote with its reference, and check them against a Bible yourself (`FLOW.md` F1) |

## What smaller models need

A local 27b model finished every task, but slowly, and it stalled wherever a
program failed late or without saying what to run next. If your agent stalls:

- Give it the exact command from the table above. Do not ask it to diagnose.
- Do not accept its proposed code changes to get past a login. In the trial
  the cause was always a profile that had never been logged in.
- Raise the model's context window well above a default such as 8192 tokens.
  `AGENTS.md`, `docs/FLOW.md` and `skills/script2film/SKILL.md` alone are about
  5,500 words (roughly 8,000 to 9,000 tokens); a small window cannot hold them
  together with a long conversation, and each later step gets slower.
- Ask for one film at a time.
- Expect it to ask before spending VideoExpress or TalkingPhotos credits.
  `AGENTS.md` requires that; an agent that does not ask is not following the
  documents.

## Reporting

If an agent gets stuck somewhere not listed here, that is most likely a gap in
the documents. Note the step (F0 to F6, or Optional A to F), the command, and
what the agent saw.
