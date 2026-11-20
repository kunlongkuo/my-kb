# Example: a small coffee shop's year

A four-line explainer of about 25 seconds: a line chart, a pie chart, a sum and a breakdown, all four drawn by code. The content is made up.
It needs no account and no key; the voice and the transcription both run on your machine.

## How to make it

Follow F0 to F6 in `docs/FLOW.md`, with `<project>` replaced by this folder (`examples/coffee`). The script (the `doc.json` of F1) is already written and reviewed, so in F1 you only run the check, and F2 runs without `--script-approved`: `expected.json` holds the fingerprint of this narration. Change a line and F2 stops until the user approves the new script.

You can make it right here: everything a film produces is listed in the `.gitignore` at the repository root (the `examples/*/…` block) and stays out of version control. To clear the outputs afterwards:

```
git clean -ndX examples/coffee    # see what would be removed
git clean -fdX examples/coffee    # remove only the ignored files (the film's outputs)
```

If you would rather not touch the repository, copy this folder somewhere else first.

## What you will see when it is done

- `cut_lecture-finance/output.mp4`: the film, with narration, subtitles and four pictures.
- Its length falls inside the `seconds` range in `expected.json` (the voice comes out a little different every time, so it will not match exactly).
- The F6 check exits 0. It may list a few "sparse cards" beats (frames with little on them); that list is a reminder and stops nothing.

## Files

| File | What it is |
|---|---|
| `doc.json` | four narration lines, four beats, the `lecture-finance` palette |
| `refs/narrator.wav`, `refs/narrator.txt` | the reference voice and the sentence it reads. It is a synthetic voice designed from a text description, not a recording or a clone of any real person |
| `refs/voice_cast.json` | the description, language (`"lang": "en"`) and seed the voice was designed from (the input of `tools/tts/design_voices.py`) |
| `expected.json` | what a right result looks like: the number of beats and lines, and the range the film's length falls in; `script_approved` is the fingerprint of the reviewed narration |

To use your own voice: point `voice.ref_wav` and `voice.ref_text` in `doc.json` at your recording (about 10 seconds) and its word-for-word text. Using someone else's voice needs that person's consent.

The words the pictures appear on (`at` in `doc.json`) are plain words, not numbers: a transcriber may write a spoken number as `100` or as `one hundred`, so the narration here leaves the numbers to the pictures.
