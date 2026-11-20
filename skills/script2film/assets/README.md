# Assets

Fonts and sound effects for doc mode (`skills/ve-director/doc/`), in two layers.
The sound effects ship with the repository (`sfx/`, files and `manifest.json` in git). The font files do not: only
`fonts/manifest.json` is in git (`.gitignore`: `assets/fonts/*`), and you download the two fonts once (below).

| Layer | Where | What goes in it |
|---|---|---|
| Bundled | `$S2F_ASSETS`, default this folder | `fonts/`: Noto Sans TC and Noto Serif TC (OFL 1.1), downloaded by you. `sfx/`: Kenney sounds (CC0), self-made ones (自製) and, in `sfx/ve-gen/`, sounds the project author generated with VideoExpress AI Sound Maker, released with this repository (MIT); all in git |
| User (optional) | `$S2F_ASSETS_LOCAL`, any folder you choose | the same layout (`sfx/` with its own `manifest.json`) for sounds you generated or found yourself, for example with `tools/assets/gen_sfx_ve.py` |

Lookup order (`doc_common.assets()` / `asset()`): the user layer first (only when `S2F_ASSETS_LOCAL` is set and the
folder exists), then the bundled layer. `doc_sfx.py` merges both `sfx/manifest.json` files, the user layer winning on
the same id, and finds each sound in its own layer's folder. Every kind in `skills/ve-director/doc/sfx_map.json` has a
bundled sound, so a fresh clone with no user layer plays them all. Music is not in either layer: a script's `"bgm"`
points at its own file, relative to the project.

The licence of each sound is in its manifest entry, and `doc_sfx.py` refuses a sound whose licence is not one it
knows (CC0, 自製, VideoExpress, or released with this repository). Where each set came from is in `NOTICE.md`.

## Fonts

The two fonts can be fetched directly (OFL 1.1): from <https://github.com/google/fonts> download
`ofl/notosanstc/NotoSansTC[wght].ttf` and `ofl/notoseriftc/NotoSerifTC[wght].ttf` and save them in `assets/fonts/` as
`NotoSansTC-Variable.ttf` and `NotoSerifTC-Variable.ttf` (checked 2026-11-15: byte-identical to the files this
project uses). `python3 tools/doctor/doctor.py` prints the same instruction, as two `curl` commands, when they are
missing.

### Optional fonts

Four more OFL 1.1 fonts are listed in `fonts/manifest.json` with `"optional": true`, each with the `url` of its
original release (checked 2026-11-20). Nothing requires them yet and the doctor does not ask for them; download the ones
you want into `assets/fonts/`:

| File | Font | Use |
|---|---|---|
| `LXGWWenKaiTC-Regular.ttf`, `LXGWWenKaiTC-Medium.ttf` | LXGW WenKai TC 霞鶩文楷 TC | scripture and quote cards |
| `LXGWWenKai-Regular.ttf` | LXGW WenKai 霞鶩文楷 | the same design for Simplified Chinese |
| `jf-openhuninn-2.1.ttf` | jf open-huninn 粉圓 | rounded title cards for vertical videos; Traditional Chinese only, no Simplified edition |

```bash
python3 -c "import json;[print(f['url']) for f in json.load(open('assets/fonts/manifest.json')) if f.get('optional')]" \
  | while read u; do curl -fL -o "assets/fonts/${u##*/}" "$u"; done
```

Fonts under other licences (for example the IPA Font License, which LXGW ZhiSong and I.Ming use) are not listed here;
keep them in your own user layer (`$S2F_ASSETS_LOCAL/fonts/`).

## Your own sounds

Make your own sounds with VideoExpress AI Sound Maker, from a list of prompts, on your own account:

```bash
export S2F_ASSETS_LOCAL=<your user layer folder>
python3 tools/assets/gen_sfx_ve.py tools/assets/sfx_prompts.example.json --dry-run   # the plan, no browser
python3 tools/assets/gen_sfx_ve.py <your prompts.json>                               # asks before using credits
```

They land in `$S2F_ASSETS_LOCAL/sfx/ve-gen/` with entries in that folder's `manifest.json`; how it works is in the
script's own help (`--help`), including what has been checked against the live site (2026-11-17: several prompts in
one run, lengths of 3, 4, 5 and 7 s, skipping sounds already made, and a stopped run downloading its sent job without
paying again). To use one for a kind, list its id in that kind's `"files"` (in `sfx_map.json`, or a
script's own `"sfx_map"` in `doc.json`). A sound with the same id as a bundled one replaces it.

If you already have a library folder (with `fonts/` and `sfx/manifest.json`) from an earlier setup,
`tools/assets/copy_from_library.py` copies its Noto fonts into `assets/fonts/` and, with `--local <folder>`, its
sounds that do not ship here into your user layer. It never writes `assets/sfx/`.

```bash
python3 tools/assets/copy_from_library.py <old library folder> --local <your user layer folder>
export S2F_ASSETS_LOCAL=<your user layer folder>
```
