# tools/drama — cutting a lip-synced short drama

For films with no narrator: every line is spoken on screen by the characters (lip-synced clips). One timeline file,
`cut.json`, describes the whole film; `drama_cut.py` turns it into a finished video or a Concat project, and can read
your Concat edits back into the file.

```
python3 tools/drama/drama_cut.py check  <cut.json>              # dialogue cut off? burned-in text? missing files?
python3 tools/drama/drama_cut.py render <cut.json>              # finished film without Concat
python3 tools/drama/drama_cut.py concat <cut.json> [--export]   # Concat project (via MCP, no window); --export also renders it
python3 tools/drama/drama_cut.py pull   <cut.json> <Concat project folder>   # read your edits back → <cut>_pulled.json
python3 tools/drama/splice_voices.py <original.mp4> <voiced-1.mp4> <voiced-2.mp4> … -o <out.mp4>
```

- **check** transcribes each dialogue shot with local whisper.cpp (`S2F_WHISPER_CPP_MODEL`, see `tools/config`) and
  compares the word count with the subtitles (CJK characters for Chinese, words for English); a line is flagged only when
  words are missing *and* speech runs into the end of the clip. It also samples three frames per picture segment for
  burned-in text (macOS Vision, optional) and checks that every source is long enough.
- **render** builds the same parts as `concat` (one picture file per shot, one wav per dialogue shot, sound effects,
  scene beds, music, subtitles), joins the pictures with ffmpeg concat, sums all sound with numpy at their start times,
  normalises with `loudnorm=I=-14:TP=-1.5:LRA=11`, and overlays subtitles drawn with Pillow (no `drawtext`/`subtitles`
  filter needed). Output: `<cut folder>/<name>.mp4` and `<name>.srt`; if either exists it writes `<name>_v2`, `_v3`, …
  Intermediate files go to `<cut folder>/.<cut stem>/render/`: `bus_dialogue.wav`, `bus_bed.wav`, `bus_music.wav`,
  `bus_sfx.wav` (each kind of sound on its own), `mix_raw.wav`, `mix.wav`, and `timeline.json` (start of every shot).
- **concat** puts the same parts on separate tracks: picture (titles and cards already drawn in), subtitles on top,
  one track per speaker, one for sound effects, one bed track per scene, and one for music.
- **pull** maps the clips back to shots by file name (`NN_<shot>.mp4`, `sfx_<k>_<name>.wav`), and reports trims,
  reordering, removed shots, moved sound effects and subtitle changes. A shot written with `sub` is written back with
  `sub`, one written with `subs` keeps `subs`.
- **splice_voices.py** joins two voice-changed versions of the same two-person clip: the k-th stretch of speech takes
  its sound from the k-th version (cuts in the middle of the pauses).

## cut.json

Paths are relative to the folder holding `cut.json` (absolute paths are used as they are).

```json
{
  "name": "my_drama",
  "fps": 30,
  "lang": "zh",
  "font": "fonts/NotoSerifTC-Variable.ttf",
  "sfx_dir": "sfx",
  "dialogue": {"stem": "vocals", "db": -18},
  "sep_dir": "work/sep",
  "scenes": {"cafe": {"bed": "auto", "db": -33}, "street": {"bed": "sfx/street.wav", "db": -30, "fade_out": 2.0}},
  "music": {"file": "music/theme.wav", "db": -31, "stop_at": "S3"},
  "shots": [
    {"id": "S0", "card": "Day one", "dur": 3.0, "sfx": [{"name": "rooster", "at": 0.6, "db": -10}]},
    {"id": "S1", "src": "clips/shot1.mp4", "in": 0, "dur": 6.0, "scene": "cafe",
     "title": {"lines": [{"text": "My Drama", "size": 110, "y": 200}], "from": 0.8, "to": 5.4}},
    {"id": "S2", "src": "clips/shot2.mp4", "in": 0.4, "dur": 6.7, "speaker": "Amy", "scene": "cafe",
     "subs": [{"text": "Three more minutes.", "from": 0.5, "to": 2.2}, {"text": "Call me, we'll talk.", "from": 3.7, "to": 5.8}],
     "pics": [{"src": "clips/shot2.mp4", "in": 0.4, "dur": 3.1},
              {"src": "clips/reaction.mp4", "in": 0, "dur": 2.6, "hflip": true},
              {"src": "clips/shot2.mp4", "in": 6.1, "dur": 1.0}]},
    {"id": "S3", "src": "clips/shot3.mp4", "in": 1.2, "dur": 4.6, "speaker": "Ben", "scene": "cafe",
     "crop": [1280, 720, 520, 40], "sub": {"text": "Sure.", "from": 0.3, "to": 1.0}},
    {"id": "END", "card": {"lines": [{"text": "The End", "size": 74, "y": 480}], "bg": "#000000"}, "dur": 4.0}
  ]
}
```

### Top level

| key | default | meaning |
|---|---|---|
| `name` | required | output file / Concat project name |
| `fps` | `30` | frame rate of cards and of every shot's picture file |
| `lang` | `"zh"` | `"zh"` or `"en"`; language passed to speech recognition in `check` |
| `font` | `<S2F_ASSETS or repo assets>/fonts/NotoSerifTC-Variable.ttf` | subtitle and card font |
| `sfx_dir` | `"sfx"` | sound effects are `<sfx_dir>/<name>.mp3` or `.wav` |
| `roomtone` | none | `{"name", "db"}`: one file from `sfx_dir` looped under the whole film (older, single-bed form) |
| `grade` | none | `"old_photo"`: `concat --export` also writes a colour-graded copy |
| `dialogue` | `{"stem": "original"}` | `stem`: `"original"` uses the clip's own sound; `"vocals"` separates the voice with demucs first (`demucs --two-stems vocals -n htdemucs`). `db`: bring each source's dialogue to this RMS level (measured over the whole source, silence excluded) before cutting |
| `sep_dir` | `<work folder>/sep` | demucs cache: `<sep_dir>/htdemucs/<source path with / replaced by _, without .mp4>/vocals.wav`. A cached result is reused; leading folders of the source path may be dropped when looking it up |
| `scenes` | none | one continuous bed per scene, see below |
| `music` | none | `{"file", "db": -31, "stop_at": "<shot id>"}`: music from 0 s, hard stop at the start of `stop_at` (0.05 s fade-in, 0.03 s fade-out); without `stop_at` it runs to the end. RMS brought to `db` |

### Shots

| key | meaning |
|---|---|
| `id` | unique shot id |
| `card` | program-drawn card instead of a clip: a string (one centred line on a dark background), or `{"lines": [{"text", "size", "y", "font"?}], "bg": "#000000"}` (white lines, centred horizontally, `y` = top of the text in pixels) |
| `src`, `in`, `dur` | source clip, in-point and length in seconds |
| `speed` | 0.5–2; takes `dur × speed` seconds of source and plays them in `dur` seconds (audio follows with atempo) |
| `zoom` | centre crop zoom |
| `hflip` | `true` mirrors the picture |
| `crop` | `[w, h, x, y]`: crop this region, then scale back to 1920×1080 (before `zoom`) |
| `speaker` | the clip's sound is dialogue; it goes on that speaker's own track. Each dialogue piece gets a 20 ms fade at both ends. Shots without a speaker carry no source sound |
| `sub` / `subs` | one subtitle `{"text", "from", "to"}` or a list of them; times are seconds within the shot (an end past the shot is cut 0.02 s before the shot ends) |
| `pics` | cutaways: `[{"src", "in", "dur", "hflip"?, "crop"?, "zoom"?}, …]`. The sound still comes from the shot's `src`, unbroken; the picture switches through the segments in order. The `dur`s must add up to the shot's `dur` (within 0.001 s), and a shot with `pics` cannot use `speed`. Still one picture file per shot |
| `title` | text over the picture: `{"lines": [{"text", "size", "y", "font"?}], "from": 0.8, "to": 5.4}`; white with a soft shadow, 0.8 s fade-in starting at `from`, 0.8 s fade-out ending at `to` |
| `scene` | scene name (must be defined in `scenes`); shots of one scene must be consecutive |
| `sfx` | `[{"name", "at", "db"}]`, `at` in seconds within the shot |
| `punch` | timed zoom `[{"zoom": 1.3, "cx": 0.5, "cy": 0.4, "from": 2, "to": 4}]` |
| `delogo` | timed blur of a box `[{"box": [x, y, w, h], "from": 1, "to": 3}]`, in output pixels |

### Scenes

```json
"scenes": {"cafe": {"bed": "auto", "db": -33}, "office": {"bed": "beds/hum.wav", "db": -34, "fade_out": 2.5}}
```

Each scene gets one bed covering its first shot to its last shot, on that scene's own track.

- `"bed": "auto"` takes the stretches with no voice (at least 0.4 s long, 0.35 s away from any speech) out of the
  source clips of the scene's dialogue shots and stitches them together. With `dialogue.stem` `"vocals"` the voice
  is detected on the demucs vocals and the bed is taken from `no_vocals`; with `"original"` both come from the clip's
  own sound. If no gap is found it stops and asks for a file instead.
- `"bed": "<file>"` uses that file.
- In both cases the material is brought to `db` (RMS), looped with a 0.5 s crossfade when it is shorter than the
  scene, faded in over 0.03 s and out over `fade_out` seconds (default 0.03).

### Timing

Each shot's picture is encoded with an exact frame count taken from the cumulative start and end of the shots
(`frame_counts`), so rounding to whole frames never adds up along the film. Sound is placed at the real start of
each picture file.

## Files

- `dramalib.py` — pure logic (format checks `check_cfg`, `subs_of`, `pics_of`, `scene_spans`, `units`, `frame_counts`,
  filters, subtitles, `pull`); tested in `tests/test_dramalib.py`.
- `drama_audio.py` — numpy sound processing (gain, fades, voice gaps, stitching, looping, mixing); tested in
  `tests/test_drama_audio.py`.
- `drama_cut.py` — the command line (ffmpeg, demucs, Concat MCP, whisper.cpp).
- `splice_voices.py` — joins voice-changed versions of a two-person clip (uses `tools/assemble/velib.py`).

Run the tests from the repository root: `python3 -m pytest -q tools/drama`.
