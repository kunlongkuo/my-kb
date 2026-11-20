# Doc mode — narrated short documentary (VOX-style)

A narrated explainer of about 1–2 minutes: one narration, a beat table cut from the narration's own word timing, one
clip per beat (a VideoExpress shot or a code-drawn shot). `doc_cut.py --render` lays them on one timeline and renders the
film, `cut_<theme>/output.mp4` (narration, burned-in subtitles, -14 LUFS): that file is a deliverable film. Concat is
optional: `doc_cut.py` also writes `cut_<theme>/plan.json`, and `tools/concat/plan2concat_mcp.py` (step 7b below) builds a
Concat project from it when the film needs the layers that are laid only there (side frame, keyword pills, chapters,
punch, grain, photo credits).
Use it when the user wants a knowledge / commentary short with voice-over, archival photos and animated diagrams,
instead of a dramatized scene (that is the regular storyboard flow in `SKILL.md`).

Origin: the 2026-10-11 test film 七十個七次 / Seventy Times Seven (audio-first beat mapping, four-part collage
prompts).

## Formats

A format is a reusable way to write and arrange a series (opening and closing, one through-line per episode, wording and
voice rules, scene variety, upload settings). A series folder holds `SERIES.md` (what is special to the series, and which
format rules it overrides) and `series.json` (upload settings); anything the series does not say falls back to the format.

- `formats/vox-host/FORMAT.md` — host-led VOX explainer (from episodes 1–10 of the author's own series); start a series from
  `formats/vox-host/make_doc_template.py`.
- `scripts/doc_build.py` builds beats (`ve`, `code`, `host`, `Q`, `tts_lines`); `scripts/doc_lint.py` checks a script
  (`make_doc.py` ends with `doc_lint.check(doc)`; `python3 scripts/doc_lint.py doc.json [--off rule ...]` on its own).

## Host placements and keyword pills (lecture-* themes)

One TalkingPhoto take of the whole narration can show the host three ways in one film (full frame: beat `"source": "clip"`;
right frame with the diagram left: `"side"`; lower-left circle: `"pip"`); which to pick per beat is in
`formats/vox-host/FORMAT.md` §7b. `doc_lint.py` reports the mix, no quota.

`"pills": [{"beat", "text", "at": phrase in that beat, "dur": 2.0, "pos": "center" | "upper" | "lower-left" | "right" | "corner"}]` puts a keyword
pill over any beat (default lower-left on a full-frame host beat, where center / upper cover the face; else center).
`corner` is a small label in the upper left, from the beat's start to its end (its `at` only checks the beat): for a
source-grade tag (「依古籍推算」), not a keyword. A long pill is moved in from the frame edge.
`side` and `pills` are laid in Concat, not burned in (the `--render` film does not show them): `doc_cut.py` writes `cut_<theme>/layers.json`, and
`tools/concat/plan2concat_mcp.py ... --layers <that file>` puts them on their own lanes (movable there).
Code beats listed in `side` are drawn shrunk into the left 1220 px (`side.zoom` 1.0-1.5 enlarges them around that area's centre; 1.3 in the first lecture film). `"ve_look"` picks the VE style (default `flat`
for every lecture-* theme, so switching palettes reuses the clips). Palettes: `lecture-light`, `lecture-dark`,
`lecture-story` (storytelling, dark), `lecture-finance` (finance / business), `lecture-food` (food),
`lecture-tech` (technology, dark), `lecture-history` (history and humanities), `lecture-faith` (faith),
all eight in `themes/lecture.json`.

Adding a palette (新增色票; checked by `tests/test_lecture.py` and `python3 tests/lecture_palette_check.py`):
1. The same 11 keys as the others (`bg`, `panel`, `fg`, `muted`, `accent`, `accent2`, `hi`, `ring`, `dim`, `font_big`, `font_ui`) plus the `light` flag.
2. `_why`: one sentence on the subject it comes from and what the main and second colours are (`light` and `dark` keep a per-pixel record in `_source` instead).
3. `_from`: where the colours were sampled, as `<repo folder>:<path in that repo>`; sample from our own material, not from another project's theme. The test looks under the folders listed in `PALETTE_SRC_ROOTS` (colon-separated, no default; unset = skipped): repo folder not there = skipped, repo there but file missing = fail.
4. Contrast (WCAG 2.1): `fg` on `bg`, `fg` on `panel` and `muted` on `bg` are each at least 4.5.
5. `accent` on `bg` is printed, not gated (`light` is 2.78): the main colour is for big numbers and shapes, not body text.

Charts colour a market move with `--up` / `--down`: `"rise": "red"` (default; Taiwan,
China, Japan) or `"green"` (US stocks) in doc.json picks which colour means up (lecture-* themes only).

## Flow

**The steps are numbered, not sequential.** Start step 5 (VE) the moment step 3 (voice) starts, with `doc_runsheet.py --estimate` (lengths guessed from the script, every guess so far long enough), and run the host take (TalkingPhoto, `doc_host.py split` → `tools/tp/tp_host.py`) alongside the VE collect as soon as the voice is done; upload the host look to TP before that (`python3 tools/tp/tp_upimg.py "<look>.jpg"`; a new series or a new look always needs it). `--estimate` counts Chinese characters: an English film sends VE after alignment. Before sending VE, do the material check (FORMAT §6 point 7); after collecting, run `ve_clipcheck.py` (`docs/FLOW.md` optional A). The general step-by-step version, with the exact commands, is `docs/FLOW.md` at the repository root: read it before starting any episode (once VE waited for the voice because this table was read as an order). The S labels in the table below are the step names the other files in this folder use.

| Step | Do | Stop? |
|---|---|---|
| 1 Topic | One dilemma, one science point, one quote; an anchor word (2–4 characters / 1–2 words) that opens as the viewer's trouble and closes redefined; a second-person hook; end on a question the viewer can answer | |
| 2 Plan | Write `doc.json` (lines + beats + shots, below). Hook beats 3–5 s; the climax line gets long gaps around it; keep facts checkable; write `facts.md` beside doc.json and set `"facts": "facts.md"` (table and rules: "facts.md" below) | **stop: show the script and the beat table; go on only when the user approves this script** (`doc_tts.py` will not run without it) |
| 3 Voice (S1–S2) | `doc_tts.py --script-approved` after the user approved the script (recorded in `script_approval.json`; the same narration needs no flag again; without approval it voices nothing and exits 4) (Qwen clone, 3 candidates a line; any `python3` works, it re-runs itself with `$S2F_QWEN_TTS_DIR/.venv/bin/python`) → `doc_voice.py` (ASR picks, joins with gaps; doc.json `"asr"`: `"local"` whisper.cpp by default, `"cloud"` Groq) | |
| 4 Align (S3) | `doc_align.py` → `final.srt`, `beats.json` (timing authority from here on; `"asr": "local"` whisper.cpp word timing into `voice.cleaned/aligned/audio.words.json`, `"cloud"` ElevenLabs Scribe, which sends the whole narration audio to ElevenLabs and falls back to whisper.cpp) | |
| 5 VE shots (S4a) | **with step 3**: `doc_runsheet.py --estimate` (after alignment: without `--estimate`) → ve-runner `--auto-pick` → `ve_collect.py --out <project>/ve_<look>` (look: doc.json `ve_look`, else `flat` for lecture-*, else the theme) → `ve_clipcheck.py` | |
| 5b Host (S5) | after step 3, alongside step 5: `doc_host.py split` → `tools/tp/tp_host.py` (several episodes: `tp_multi.py`) → `doc_host.py join`; details in `tools/tp/README.md` | |
| 6 Code shots (S4b) | `doc_code.py --render` (checks every trigger phrase first; renders with HyperFrames from the repo root: `npm ci` once) | |
| 7 Cut (S6) | `doc_sfx.py --report` (sfx_on) → `doc_cut.py --render`: writes `cut_<theme>/plan.json` for Concat and a base mp4 `cut_<theme>/output.mp4` (subtitles and narration; the music bed and the sound-effect bed when doc.json has `bgm` / `sfx_on`, the synthesized wind bed when it has no `bgm`; loudness-normalized to -14 LUFS). `doc_cut.py --name` names the timeline | |
| 7b Concat (S7, optional) | `tools/concat/plan2concat_mcp.py cut_<theme>/plan.json ... --export`: the film with the layers only Concat lays (side, pills, chapters, punch, grain, photo credits); without them the step 7 `output.mp4` is the film (`docs/FLOW.md` optional D) | |
| 8 Check (S8) | `check.py` and its frame sheet (`docs/FLOW.md` F6): a frame at each beat's first word (+0.15 s) must already match the words | numbers fail: do not upload; a wrong VE shot goes back to step 5 |
| 9 Upload (S9) | `docs/FLOW.md` optional F (`yt_upload.py`; add `--synthetic` and the channel account the series names) | |

Commands with their exact flags: `docs/FLOW.md`. Environment
(full list in the header of `scripts/doc_common.py`; no Cutline and no API key are needed from voice to the base render,
checked in a clean clone by `tools/check-standalone.sh`):

- `npm ci` once in the repo root installs HyperFrames (pinned in `package.json`) into `node_modules/`; it runs with a
  Node 22+ `node` from PATH. `S2F_HF_BIN` (optional) points at another HyperFrames package folder or entry script.
- `S2F_QWEN_TTS_DIR` (qwen3-tts with its `.venv`; models in `S2F_QWEN_TTS_MODELS`, default `$S2F_QWEN_TTS_DIR/../_models`).
- `S2F_WHISPER_CPP_MODEL` (the whisper.cpp model `ggml-large-v3-turbo.bin`; `whisper-cli` from PATH or `S2F_WHISPER_CLI`): with doc.json `"asr": "local"` (the default) `doc_voice`
  picks takes and `doc_align` takes word timing with it, no keys, no audio sent out.
- `"asr": "cloud"` uses two online services: Groq Whisper to pick takes (`GROQ_API_KEY`; every candidate take is sent to
  Groq) and ElevenLabs Scribe for word timing (`ELEVENLABS_API_KEY`; the whole joined narration is sent to ElevenLabs;
  model `scribe_v2`, or `S2F_SCRIBE_MODEL`). Groq needs its key (it stops without one) and hands the remaining takes to
  whisper.cpp when it is rate-limited; Scribe falls back to whisper.cpp when it fails or has no key (both fallbacks need
  `S2F_WHISPER_CPP_MODEL`). Keys come from
  the environment or `~/.config/script2film/secrets.json` (JSON, the key names as above). ElevenLabs' free plan has a
  usage cap, and its terms restrict commercial use of what the free plan produces: check the current numbers and terms
  on ElevenLabs' official pricing page before using it for a published film.
- `S2F_ASSETS` (the bundled fonts and sounds, default the repo root's `assets/`) and `S2F_ASSETS_LOCAL` (optional user
  layer, looked in first: your own sounds); filling them: `assets/README.md`.

Rendering needs no network: GSAP is an npm dependency (`npm ci` once at the repo root) and is copied next to every
page. `doc_tts.py` after a script edit voices only the
changed lines, once the user has approved the edited script; `doc_align.py --retime` after the narration changes (the old flag `--rescribe` also works).

TalkingPhoto High Quality renders at most 1 minute (at least 10 s): `doc_host.py split` cuts `tts/voice.wav` into parts in
the pauses between lines, `tools/tp/tp_host.py` uploads, renders and downloads them to `host/parts/partK.mp4`,
and `join` builds `host/tp_host.mp4` on the subtitle timeline. Point `clip` / `pip` at `host/tp_host.mp4`.
`"bgm": {"src", "lufs", "credit"}` puts a music bed on its own track in `plan.json` and mixes it into the `--render` film (-40 LUFS by default; faded in and out); put the credit line in the post (CC BY). A livelier bed
(tutorials): `"duck"` (0-12 dB) lowers it while the narration speaks, `"lift"` [beat ids] lets it
back up under titles, demos and the close (pauses are too short to lift it on their own), `"drops"` [beat ids] stops it
for `"drop_s"` (1-4 s, default 2.5) from the start of a question or key claim. `"lufs"` is the bed before ducking.
A bed louder than -30 LUFS with no `"duck"` stops the cut (2026-11-11: a -20 bed without duck covered the narration).
Sound effects: `"sfx_on": true` makes `doc_code` save each code beat's sound marks
(`code_<theme>/<id>.sfx.json`; the scenes call `sfx(kind, t)` on a paper drop, a count landing, a highlighter swipe,
a list item, a click...) and `doc_cut` put `sfx/sfx_bed.wav` on its own track; `doc_sfx.py` builds that track from
three sources: the scenes' marks plus a tear on each `"wipes"` cut, the series word list (`"sfx_words"`: a json
`{word: kind}` relative to the project, whole words of 2+ characters, e.g. 紅海 → water), and `"sfx_add"`
`[{"beat", "at", "kind"}]`. `"sfx_off"`: `["B12", "B12#kind:paper", "B12#word:紅海"]` removes. At most 3 visual sounds
a beat; a word sound is dropped within 1 s of a visual one and within 8 s of the previous word sound. `--report` lists
every sound with the words around it and why each dropped one was dropped. Kinds, files and volumes: `sfx_map.json`
(only CC0, 自製, VideoExpress or with-this-repository sounds; every kind has a sound in `assets/sfx`, which ships with
the repository; a kind whose files are all missing is skipped and reported). Not for that daily short series.
`"sub_bg": {"color": "#000000", "alpha": 0.7}` puts the subtitles on a dark box (white text) in `plan.json` and the
render, in place of the mist.

A second language reuses the VE clips (they carry no text): copy `ve_<look>/` into the new project. A clip a little
shorter than its new window is slowed down (`max_stretch`, default 1.2×, at most 1.5×) instead of freezing.

## doc.json

```
{
  "title": "...", "lang": "zh" | "en", "theme": "lecture-light" | "collage" | ..., "speaker": "narrator",   // the ten names are listed under the block
  "asr": "local" | "cloud",                                          // optional: word timing and take picks on this machine (default) or Groq + Scribe
  "palette": "出埃及與曠野",                                         // optional, collage only: an era palette from doc_themes.PALETTES
  "voice": {"ref_wav": "refs/x.wav", "ref_text": "refs/x.txt", "seed": 11, "tail_fade": 0.08},   // tail_fade optional: fade-out on each line end
  "gaps": {"default": 0.32, "after": {"6": 0.9, "7": 1.6}},        // pause after line n (seconds)
  "end_hold": 1.0,                                                  // optional: seconds of picture after the last word (default 1.0)
  "sub_highlight": {"words": ["VideoExpress"], "color": "#D65440"},  // optional: these words bold and coloured in the burned subtitles
  "lines": [{"text": "...", "tts": "optional pronunciation-safe text", "speaker": "optional: a name from voices"}],
  "voices": {"老闆": {"ref_wav": "refs/keeper.wav", "ref_text": "refs/keeper.txt", "seed": 21}},   // optional: a second voice for dialogue
  "en": ["...", "..."],                                              // optional: one English subtitle per line, under the Chinese (Concat layer + subtitles_en.srt)
  "zh": ["...", "..."],                                              // optional, only with "lang": "en": one Chinese line per script line shown as the main subtitle (cut into screens, timed by character count within the line's span), the English narration goes underneath; do not set "en" as well
  "beats": [
    {"id": "B1", "lines": [1], "source": "code", "scene": "seed_dot", "veil": [true, true], "params": {...}},
    {"id": "B2", "lines": [2], "source": "ve", "shot": "bench_apart"},
    {"id": "B6", "lines": [7], "source": "code", "scene": "burst_title", "start": "after_prev", "params": {...}}
  ],
  "shots": {"bench_apart": {"t2i": [scene, setting], "scene": "...", "ident": "...", "acts": [[0, 0.5, "..."]], "camera": "Static wide shot, locked-off, no camera movement.", "no_people": true}}   // no_people: drop the look's people clause (flat adds bystanders otherwise)
}
```

Dialogue: a line with `"speaker"` naming an entry of `"voices"` is cloned from that entry's reference (its `seed`,
`tail_fade` and `post` too when it gives them; anything it leaves out comes from `"voice"`); every other line uses
`"voice"`. `doc_voice.py` matches pitch within each speaker, `tts/lines.json` records who says each line, and the
speaker is part of the approved script (changing who says a line needs approval again). `doc_lint.py` reports a speaker
with no voice and a voice without `ref_wav` or `ref_text`. Design a voice that belongs to nobody with `tools/tts/design_voices.py`.

`"theme"` is the palette of the whole film (code shots, subtitles, pills). `doc_code.py` and `doc_cut.py` take
`--theme=<name>` to use another one for a run (cut with the name the code shots were drawn with: `doc_cut.py` reads
`code_<theme>/`); a name not in this list stops both. The ten names (the same as the gallery page of the website):

| `theme` | Look |
|---|---|
| `lecture-light` | flat teaching panels, light |
| `lecture-dark` | flat teaching panels, dark |
| `lecture-story` | storytelling, dark |
| `lecture-finance` | finance and business; `examples/coffee` and `examples/brewing` use it |
| `lecture-food` | food |
| `lecture-tech` | technology, dark |
| `lecture-history` | history and humanities, an old-map paper ground |
| `lecture-faith` | faith |
| `collage` | the VOX paper collage look (torn paper, halftone cut-outs, tape); `examples/seventy-times-seven.*.json` use it; the only theme that takes `"palette"` |
| `live` | documentary realism: photoreal VE shots, dark infographic code shots |
| `dark-gold` | dark warm ground, gold hairline frames, serif titles (VE look `live`) |
| `newsroom` | news desk: charcoal ground with a faint grid, cards with a thick left bar, captions as yellow label strips (VE look `live`) |
| `vintage-poster` | old poster: yellowed paper with halftone, thick black frames with an offset colour block (misregistered print) (VE look `flat`) |
| `editorial-serif` | magazine page: cream ground, serif titles, rules above and below instead of boxes (VE look `collage`) |
| `cinematic-dark` | film: near-black ground with a heavy vignette, soft glow on the words, cards as faint dark panels with no border (VE look `live`) |

The eight `lecture-*` colours are in `themes/lecture.json` (how to add one: "Adding a palette" above); `collage` and `live`
are defined in `scripts/doc_themes.py`; the five styled themes are in `themes/styles.json`: a palette with the same keys and
contrast rule as "Adding a palette", a `shape` and a `ground` named from `SHAPES` / `GROUNDS` in `scripts/doc_themes.py`, and
`ve`, their VE look (checked by `tests/test_styles.py`). A new styled theme changes all three layers, not only the colours.
To see three themes on an episode's own beats before choosing, run `scripts/doc_theme_preview.py` (`docs/FLOW.md` optional G).
Each theme also picks the look of the VE shots (`ve_look`, above).

Several beats per line: `"from": "<phrase>"` opens a beat on that phrase inside its first line (the line's earlier
beat ends there), so a sentence can cut every 1-2 s; trigger tokens are trimmed to each beat's own span.
A host take: `"source": "clip", "clip": "host/<full-narration take>.mp4", "clip_sync": true` cuts that beat's window
out of a TalkingPhoto take rendered on the whole narration (lips stay on the voice); `"vf"` is its ffmpeg scale filter.
`"clip_in"` (seconds) cuts from that point of the take instead of the beat's start: after the pauses around other lines
were lengthened, a take made on the earlier narration still fits the host's own lines (they did not change length).
`"pip"` (top level) puts the same take in a round frame over the listed beats, interleaved:
`{"clip", "beats", "crop", "d", "ring", "vf"}`. `"sticker"`: a corner badge carried over the next beats, cut from the
last frame of a code shot that ends on it (`merge_bubble` `badge`). `"wipes"`: [beat ids] get a torn-paper sheet wiping
across the cut into them (see `doc_cut.py overlays`). Host takes: frame the master `cinematic medium shot framed from
head to waist` (VE platform rule) and pick TalkingPhoto's High Quality style, not Closeup; leave the take ungraded.

Time params name a phrase from the beat's own narration (`"two programs"`, `"兩個程式"`), or seconds, or
`{"w": phrase, "d": offset, "f": fallback}`. `doc_code.py` refuses to run when a phrase is not in the beat.
Examples: `examples/seventy-times-seven.en.json` (and its Chinese twin in the same folder).

## facts.md: the fact list

Optional for the program, asked for by the vox-host format (`formats/vox-host/FORMAT.md` §9, in Chinese). With
`"facts": "facts.md"` in doc.json (a path relative to the project folder), `doc_lint.py` and the start checklist
(`tools/checklist`) check what the code shots put on screen against one Markdown table in that file. Without the key
nothing is checked and no file is needed.

The table is the first one whose header row has a `畫面` (`on screen`) column. The header must name these five columns
(any order), each by its Chinese name exactly as written or by its English name in any case (`On screen`, `on screen`);
the two can be mixed in one header. Its rows are the `|` lines after the separator line, up to the first line that is not one:

| Column | English name | What to write |
|---|---|---|
| `畫面` | `on screen` | the text or number as it appears in the shot |
| `等級` | `tier` | exactly one of `原始` / `primary` (primary source), `權威二手` / `secondary` (authoritative secondary source), `線索` / `lead` (a lead, not yet confirmed); the English words in any case. Any other value fails; a row marked `線索` / `lead` fails when a beat uses it: a lead does not go on screen |
| `出處` | `source` | site or publication and date; a Bible reference as book chapter:verse (below) |
| `原文摘錄` | `excerpt` | the words copied from the source |
| `備註` | `note` | the beat id (`B4`) for numbers and charts, plus anything else |

What needs a row (code beats only; a beat with `"fact": false` in its params is skipped):

- `stat_count`: a row whose `備註` names the beat and whose `畫面` has the `value`, written the same way (`1200`, not `1,200`).
- `pie`, `line_chart`, `breakdown`: a row whose `備註` names the beat (one row per chart, not one per number). `formula`
  and the other scenes are not checked.
- `quote_card`: a row whose `畫面` is the card's `text` (spaces and punctuation ignored; letters must match, case included).
- A Bible reference written anywhere in a code beat's params, with a Chinese (CUV) book name or its abbreviation
  (`出埃及記 14:13`, `出 14:13`; a chapter alone does not count): a row whose `出處` covers it. When a `quote_card`'s `by` is
  such a reference, every part of its text (split at `……`) must also be in that row's `原文摘錄`.

English films can use the English column names and tiers and write every cell in English. Bible book names are only
recognised in Chinese: a reference with an English book name (`Exodus 14:13`) is not recognised as a Bible reference, so
it is neither required nor checked against the excerpt: show such quotes to the user with their references. Messages
name a column or tier both ways, e.g. `備註/note`.

A minimal example: `examples/coffee/doc.json` with `"facts": "facts.md"` added and this `facts.md` beside it passes
`doc_lint.py` (`doc_lint: ok`); without the B4 row it exits 1 with `facts: B4 chart data has no row in facts.md (備註/note naming B4)`.

```
| On screen | Tier | Source | Excerpt | Note |
|---|---|---|---|---|
| Monthly sales, Mar to Aug | primary | the shop's own sales ledger, 2026 | Mar 20k, Apr 21k, May 20k, Jun 28k, Jul 35k, Aug 42k | B1 line chart |
| Where the costs go | primary | the shop's own cost sheet, 2026 | beans 45%, rent 30%, staff 25% | B2 pie |
| Profit split | primary | the shop's own sales ledger, 2026 | coffee 8k, pastries 2k | B4 breakdown |
```

The same table with the Chinese names (`| 畫面 | 等級 | 出處 | 原文摘錄 | 備註 |`, tier `原始`) reads the same.

## Scene templates (`scenes/`)

| Template | Shows | Params |
|---|---|---|
| `seed_dot` | hook: one dot lands, a wash breathes, the dot pulses on the anchor word | `sigh` [2 phrases], `pulse` |
| `split_duel` | a split screen frame, two dots, a strike and a strike back | `appear`, `hits` [2] |
| `cover` | an episode's title card under the spoken opening, right of centre so a `pip` host fits lower-left: small series label, big title with red tape, the range on a card, a red stamp | `series`, `title`, `sub`, `sub_at`, `badge`, `at`, `cx`, `size` |
| `burst_title` | climax: dim during the breath, hold, burst on the word; big word + term; collage puts red paper behind it (a disc if the word fits, else a strip) | `word`, `big`, `term`, `term_sub`, `big_size` |
| `exchange` | two agents trading moves on one board; consecutive exchange shots cut as one continuous board | `mode`: coop (`appear`, `loop`), mirror (`a`, `b`), spiral (`good`, `bad`, `revenge`, `loop`), forgive (`other`, `attack`, `forgive`), reconcile (`start`, `pull`, `far`) |
| `photo` | one archival still (everything as layers) | — (a photo layer can add `fg`: the same photo cut out on a transparent ground, for a 2.5D push; `leak`: a warm light leak drifts across) |
| `object_draw` | a closing object drawn stroke by stroke | `preset` ("chair") or `paths` |
| `stat_count` | one number that matters, counting up as it is said | `value`, `from`, `decimals`, `prefix`, `suffix`, `caption`, `at`, `caption_at`, `dur`, `hot`, `slam` (lands at its value instead of counting) |
| `timeline` | a line with dated markers appearing as each date is mentioned; a long line (one series-wide line of eras) can be shown a stretch at a time and slide from one stretch to the next | `items` [{`date`, `text`, `at`}] (2-6; up to 12 with `window`), `hot` (index in red), `window` [first, last] (the 2-6 items the frame shows at the end), `from` [first, last] (as many items, shown first; their default `at` is 0.2 s apart), `pan_at` (default 1.0 s; only with `from`) |
| `compare` | two columns (A vs B), an optional verdict marks one | `left` / `right` {`title`, `text`, `at`} or {`title`, `items` [{`text`, `at`, `hot`}]} (a ledger growing one line per mention under each title), `verdict` {`side`, `text`, `at`}, `big` (about twice the words, for a rank or a number), `slam` (with `big`: the texts land instead of fading in) |
| `countdown` | a clock running from 0 to how long something took, a bar draining under it, the end in the accent colour (reconstructing an event) | `value` (seconds), `from`, `label`, `at`, `dur` (seconds on screen, default 3; `doc_lint.py --beats` reports a clock that has not stopped 0.5 s before the beat ends), `hot` (default true), `bar` (default true), `caption`, `caption_at` |
| `grid_hot` | numbered cells appearing one after another, then one turns accent and the rest dim (one of many: the 17th of 50 approvals) | `count` (2-100), `cols` (default 10), `title`, `at`, `stagger` (seconds, default 1.2), `hot` (1-based), `hot_at`, `fmt` (default `#{n}`), `caption`, `caption_at` |
| `credits` | the closing page: credit groups roll up like film end credits | `title`, `groups` [{`head`, `lines`}], `at`, `x` (column centre, default 1060) |
| `bars` | a small bar chart, each bar grows when its label is said | `items` [{`label`, `value`, `at`, `dir` ("up" / "down": rising / falling colour)}], `max`, `hot`, `unit`, `title` |
| `line_chart` | a trend: the line draws as far as the narration has got | `labels` (2-24), `series` [{`name`, `values`, `color`}] (1-3), `reveal` [{`upto`, `at`}], `marks` [{`i`, `series`, `text`, `at`}] (at most 4), `band` {`from`, `to`, `label`}, `min`, `max`, `unit`, `hot`, `title` |
| `pie` | what something is made of: slices sweep open as each is said, legend on the right | `items` [{`label`, `value`, `at`}] (2-6), `donut` (0-0.7, default 0.55; 0 = solid), `focus` [{`i`, `at`}], `show` ("percent" / "value"), `unit`, `center` {`text`, `sub`, `at`}, `hot`, `title` |
| `formula` | a formula or a chain of cause and effect in one row of large words; with a rewrite, 「不是 A，而是 B」: A is struck and B is written in red above it | `terms` [{`text`, `sub`, `at`, `hot`}] (2-5; 1 when it carries a strike with `to`), `ops` (= + − × ÷ → > <), `focus` [{`i`, `at`}], `strike` [{`i`, `at`, `to`, `to_at`}] (`to`: the new words, about 22 characters at most; `to_at` default 0.4 s after the line), `title`, `note` |
| `breakdown` | one quantity split into its parts, optionally a second level | `root` {`text`, `value`, `at`}, `parts` [{`text`, `value`, `op`, `at`, `hot`, `parts`}] (2-5; second level 2-3, at most 6 in all), `unit`, `focus` [{`id`, `at`}], `title` |
| `list_reveal` | a short list built up item by item | `title`, `items` [{`text`, `at`}], `hot`, `big` (larger words for a 2-3 item list). Keep each item to one line: measured 2026-11-17 with the project's fonts, one line holds about 33 English characters or 16 Chinese characters with `big` (76 px), about 48 or 21 without it (54 px). A longer item wraps inside its card (cards stop 100 px short of the right edge) and pushes the items below it down; if the list would then reach the bottom 200 px, the words and spacing of every item shrink together, to 60 % at most, until it fits. A list that still does not fit has too much text for one card |
| `map_route` | a sketch map: faint coasts, then a route drawn stop by stop as each place is said | `land` [svg path d], `stops` [{`name`, `x`, `y`, `at`, `side`}], `hot`, `title`, `note`, `base` (an old or modern map under the route: {`src`, `size`, `crop` [x, y, w, h], `kind` old / modern, `credit`, `dim`, `push`}; stops and land are then pixels on the map, the crop is fitted into the frame and the picture pushes in on the hot stop; a modern map adds 今日位置示意 to the note. Build it with `doc_build.map_route(key, crop, stops)` from the series map library `<series>/maps/maps.json`, which copies the image into the episode) |
| `flow` | how something travels (an intrusion spreading, a path taken in order, money pouring out, two routes side by side): nodes (cards with a filled icon or a VE still) joined by links; as each step is said a glowing packet runs along its link, the node it reaches ripples and lights up, packets keep flowing after that. Four looks that read differently, so consecutive diagrams in one film should not share one: `web` (light grid, round badges, dashed red links that march), `pipe` (tiles on one glowing rail, times above; made for a dark `bg_video`; on a light palette such as `lecture-food` the tiles stay dark and the labels, times and note under and above them take the palette's text colours, a reached `hot` node's label red; `streams` does the same), `streams` (ribbons of different widths pouring into one sink, a counter on each), `lanes` (two tracks, a shutter drops on one) | `look`, `nodes` [{`id`, `x`, `y` (y ≤ 860), `label`, `sub`, `icon` laptop / ai / container / stamp / chain / wallet / target / lock / shield / coin, or `src` a picture, `at`, `hot`, `time`, `color`, `size`, `side` right, `sink`}], `links` [{`from`, `to`, `at`, `color`, `w`, `bend`, `label`, `count` {`value`, `prefix`, `suffix`, `decimals`, `at`}}], `tag` {`text`, `at`, `color`}, `block` {`link`, `at`, `label`}, `note`, `note_at`, `note_xy`. A node shows when its first link arrives unless it has `at`. `doc_code.py` checks ids, links, icons and positions before rendering |
| `relation` | who (or what) is tied to whom: name cards appear as each is said, the ties draw in with a short label, a focus dims the rest. People (a family, two camps, a teacher and pupils) or things (a cause and its effects, a company and its parts). `look` "board": a clue board (cork ground, pinned paper notes, instant photos, red string from pin to pin), same layout and checks | `look`, `nodes` [{`id`, `label`, `sub`, `at`, `hot`, `src` (round picture above the name), `x`, `y` (y 120-820)}] or `rows` [[id, ...], ...] (automatic tree layout, top row first; a row too wide for the even spread is spread by the cards' widths), `links` [{`from`, `to`, `kind` tree / line / dash (broken or refused) / arrow, `label`, `at`, `hot`}], `focus` {`ids`, `at`}, `title`, `title_at`, `note`, `note_at`. A link draws just after the later of its two cards unless it has `at`. `doc_code.py` checks ids, rows, links, kinds and positions before rendering, and stops when two cards overlap or one runs off the frame once built (shorten the labels, split the row, or place the cards with `x` / `y`) |
| `web_evidence` | a still screenshot of a real page (official site, README, announcement, news headline) cropped to the part that matters, the spoken words swiped by a highlighter as they are said, the source under it | `src` (png / jpg), `crop` [x, y, w, h] (source pixels), `source` (required: site or outlet and date), `marks` [{`box` [x, y, w, h] source pixels, `at`}], `at`, `push` (default 1.03), `scroll` [{`y`, `at`, `dur`}] (a long stitched page glides so row `y` reaches the window top; `crop` is the window; build the page and the mark boxes with `scripts/doc_evidence.py`) |
| `ve_annotate` | a VE shot plays, freezes on one frame (flash, punch, colour drops), gets a ring, an arrow and one note, then plays on | `src` (VE clip), `in`, `freeze` (time or phrase), `hold` (default 2.2 s), `rings` [{`x`, `y`, `r`, `ry`}], `arrows` [{`from`, `to`, `bend`}], `note` {`text`, `x`, `y`} |
| `quote_card` | a full-screen quotation with its source; `reveal` "blur": the words wait on the card as a faint blur and come clear one character after another as the narration says them (a part the voice does not say follows the part before it) | `text`, `by`, `at`, `size`, `reveal`, `photo`: one still {`src`, `rect`, `rot`, `cap`, `push`} or two `[{...}, {...}]`; without `rect` the stills are laid out large (two: upper left and lower right, opposite tilts, the quote strip over both) and push in slowly |
| `merge_bubble` | one company swallows another: bubble B is pulled into bubble A and stays nested; a price under them | `a` / `b` {`name`, `sub`, `color`}, `a_at`, `b_at`, `merge_at`, `value` {`text`, `at`}, `badge` {`at`, `s`, `x`, `y`} (shrink to a corner) |
| `screen_step` | a recorded screen (or a screenshot) with each step marked as it is said: the rest dims, a box rings the element, a curved arrow from a numbered label | `src` (doc_screen `screen.webm` + `log`, or a png), `log`, `clip` [from, to] (≤ 10 s; default: the first click lands on its phrase), `frame` (`browser` / `none`), `url_text`, `steps` [{`n`, `label`, `at`, `box` [x, y, w, h] or `step` (log step number)}], `zoom` (push in on each step up to this scale, pan to the next, pull back after the last) |

Any drawn scene can sit on a VE live-action clip: the beat's `"bg_video": {"src": "ve_real/shot3.mp4", "tone": "light" | "dark" | "full", "in": 0}`. `light` greys the clip and washes it with the theme's paper colour (ordinary beats keep the channel's look); `dark` dims it and draws the scene in `lecture-dark` (keep it for reconstructions and turns, a few per film). `full` leaves the clip as it is, full size: footage with one small card on it (`photo` scene + `label`). The clip is cut to the beat and played forward then backward (slowed if needed) when the beat is longer than the clip.

**Pick by the job, then ask what it adds.** Choose the card from what the line needs to show, never from the list:

| The line needs to show | Card | Elevates when | Slop when |
|---|---|---|---|
| where, how far | `map_route` (old map base) | the distance or the route is the story | a map as a title backdrop |
| when, in what order | `timeline` | the order drives the story | dates flying past as decoration |
| how much, how many | `stat_count`, `bars`, `grid_hot` | one number is the turn; one comparison the viewer feels | a board of numbers nobody reads |
| who with whom | `relation` | the tie (or the refusal) is the point | every name on screen with a line |
| how it travels, in what steps | `flow`, `list_reveal` | the mechanism is the plot | a diagram of something the voice already made plain |
| the document says it | `web_evidence`, `quote_card` | the page is the evidence | a highlighter on every caption |
| a thing inside a picture | `ve_annotate` | the viewer would miss it | rings on what is obvious |

Each code shot must answer, in one line on the plan: "what does this tell that the picture alone could not?" One that cannot is
cut, not polished. One card used for several beats in a row as wallpaper, or a card that only repeats the voice word for word,
is slop. The sounds of a drawn shot land on its actions (`sfx()` marks → `doc_sfx.py`). Collage theme reference values:
torn-paper teeth 2–5 px, cut-out shadow 6–10 px, marker stroke 6–10 px.

Layers on any scene: `photos` [{`src`, `rect` [x, y, w, h], `rot`, `cap`, `at`, `cap_at`, `push`, `accent_at`, `exit`}],
`label` {`text`, `sub`, `at`}, `quote` {`text`, `at`, `top`, `cx` (default 960)}. Leave the bottom 200 px free for subtitles.
`drift`: `quote_card`, `cover`, `stat_count` and `compare` push the whole picture in to 1.10 over the beat (`timeline` 1.03: its row
runs close to the edges), so they do not hold still once their animation ends. `drift` takes another scale or `false`; a photo that already pushes (a `quote_card` photo, `photos`
with `push`) turns it off.
New template: add `scenes/<name>.js` registering `SCENES.<name> = p => {...}` with the helpers in `lib/lib.js`
(`dot`, `stroke`/`draw`, `photo`, `box`/`popIn`/`hotLine`, `at`), list its time params in `TIME_KEYS` (`doc_code.py`),
and add a row here.

## A new topic

1. Write the script (step 1 of the flow) and split it into beats: one visual idea per beat, 3–10 s of narration.
2. For each beat pick a template with the table above (or a VE shot), fill its params, and point every time param at a
   phrase that is really in that beat's narration. Copy `examples/seventy-times-seven.*.json` as the starting file.
3. Collect archival images into `<project>/assets/` with `CREDITS.md`.
4. Run the commands. `doc_code.py` stops on a missing phrase or a page script error before you look at anything.
5. A visual no template covers: add `scenes/<name>.js` (below), try it on a fake `beats.json` (tokens can be invented:
   `[[word, seconds], ...]`) before using it in a film.

## Rules (learned)

- Real photos are code shots (halftone cutout, caption, slow push). Never send a real person's photo to a video model.
- Archival sources: Wikimedia Commons, check the license per file and the subject (a same-name voice actor came up for
  "Robert Axelrod"); CC BY / BY-SA need a credit line; keep `assets/CREDITS.md` in the project. Other open collections
  with catalogue records: Library of Congress,
  Smithsonian Open Access (CC0), Rijksmuseum (CC0), NARA, Europeana (rights per item). CC0, public domain and credited
  CC BY are fine; "no known restrictions", CC BY-SA and other terms: name the terms to the user and ask first.
- More sources (searched 2026-10-29): The Met Open Access (CC0, ~490k works), Art Institute of Chicago (CC0, filter
  "Public Domain"), National Gallery of Art (open access, up to 4000 px): old master biblical paintings. Getty Open
  Content: licence not yet confirmed, check before use. Pexels photos and video (Pexels License: free, commercial use,
  no credit; logos and recognisable people keep their own rights). Taiwan government sites such as the Executive Yuan
  (Open Government Data License v1: credit the agency, year and dataset). NASA (free, but nothing that reads as NASA
  endorsing; no astronaut likeness in ads). Internet Archive / Prelinger films: only some are public domain and the
  archive grants no permission, check each. Flickr Commons "no known copyright restrictions" is not a licence (some
  institutions add no-commercial terms): ask first, as above.
- Media reports (Taiwan Copyright Act art. 52 quotation for commentary: your own work around it, related and separable,
  source named, judged case by case, TIPO 2026-01; YouTube Content ID claims regardless of fair use): a headline or a
  few lines of an article or an official announcement as a `web_evidence` screenshot, with the outlet and date, is fine.
  A series may opt into longer excerpts (several paragraphs, scrolled within the beat; ads and photos cut out with
  `doc_evidence.py`): keep the source line on screen and the excerpt no longer than its beat.
  News agency or broadcaster photos and video (AP, Reuters, Getty, TV): do not use.
- A real photo turns the narration into a factual claim: rewrite the line to match the record (the feud line became
  "decades", not "three generations").
- VE shots: camera locked-off. A pan walked both people out of frame and a pull-back faded the scene to blank paper.
- VE images and clips carry no text; every word on screen is drawn by code (the scenes, the subtitles, the Concat layers).
- Ink-wash was tried and rejected for this kind of film; collage (official VOX look) is the default, live the alternative.
- Pick TTS takes with ASR, but a low score is often a homophone (程式/城市, 報復/抱負), not a misreading.
- Chinese TTS input goes in as Simplified; subtitles stay Traditional.
- A word the TTS splits apart (撒但 read as 撒／但是) gets a homophone in the line's `"tts"` (撒旦); the subtitle keeps the
  script's spelling.
- No em dash (——, —) in narration or on screen: it reads as AI writing (2026-10-21). quote_card shows the source alone.
- burst_title's `word` opens its line (`big` may show another word): the shot drops the line's subtitle and stays dark
  until the word, so a word mid-line leaves the voice over an empty frame (2026-10-21, 1–2 s twice). doc_code rejects it.
- A scene param must not reuse a layer name (`photos`, `label`, `quote`): `stat_count` once took `label` as a string,
  the layer code read the string's built-in `.at` as a time and the whole page script died while the render went on.
- GSAP: no `fromTo` on layers that appear later without `immediateRender: false` (the start value applies at t = 0).
- SVG filters: `userSpaceOnUse` and a region that extends into negative coordinates.

## Screen capture

`python3 scripts/doc_screen.py screen/<name>.steps.json --out screen/<name> [--dry] [--profile <signed-in Chrome profile>]` records a browser walkthrough
headless at 1920 x 1080: `screen.webm`, `stepNN.png` (the page just before each step) and `log.json` (each step's time and
the element's box), which `screen_step` reads. steps.json: `{"url", "steps": [{"do": "goto", "url"} | {"do": "click",
"sel"} | {"do": "type", "sel", "text"} | {"do": "scroll", "y"} | {"do": "wait", "ms"}]}`, each step may carry `say` (its
narration line); a url without a scheme is a file next to steps.json. Run `--dry` first and show the user the page
list. A login page (an enabled, visible password field, or login / signin / auth in the url path) stops the run with exit 3
and keeps nothing: it never types into one. `--profile` records a site you are signed in to from a throwaway copy of that
profile (the original is never locked or changed); blur account details in the recording before using it. Check a recording with `tests/screen_sync_check.py` (the selftest page) and a
rendered shot with `tests/screen_step_check.py <project> <beat>`.

## Files

`lib/template.html` (page), `lib/lib.js` (timing, drawing, photo layers), `scenes/*.js`, `scripts/doc_*.py`
(`doc_screen.py`: screen recording; `doc_evidence.py`: a long `web_evidence` page stitched from a full-page screenshot, highlight boxes found by OCR;
`doc_thumb.py`: the episode's 1280×720 YouTube thumbnail from doc.json `thumb`, credit line from `assets/CREDITS.md`, FORMAT §8),
`scripts/doc_themes.py` (CODE_THEMES for code shots, VE_THEMES for prompt style blocks), `tests/` (`python3 -m pytest -q tests` from this folder; no API key needed; the fonts must be in the asset layers, and `npm ci` done: `test_hyperframes.py` checks the installed package).
In this repo: `tools/assemble/assemble.py` (cuts the clips into one picture track, called by `doc_cut.py`), `tools/assemble/cut2plan.py` (writes `plan.json`), `tools/concat/plan2concat_mcp.py` (Concat assembly and export), `assets/` (fonts, sounds).
External: qwen3-tts, whisper.cpp, ve-runner, ElevenLabs Scribe and Groq (optional, `"asr": "cloud"`),
and in this repository `tools/tp/` (TalkingPhoto host), `tools/nightly/` (checks, upload metadata) and `tools/drama/` (lip-synced drama cut).
