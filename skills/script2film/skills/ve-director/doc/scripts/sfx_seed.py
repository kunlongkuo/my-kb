"""Add doc-mode sound effects to the bundled asset layer ($S2F_ASSETS/sfx, default <repo>/assets/sfx; manifest.json = the
licence record): Kenney packs (CC0) from a downloaded folder, and five sounds synthesized with ffmpeg (自製).

  python3 sfx_seed.py kenney <folder with the pack's .ogg files> <pack name, e.g. "Impact Sounds"> <source note>
  python3 sfx_seed.py synth
The manifest is copied to manifest.<date>.json before the first write of the day. Re-running replaces entries by id.
(2026-10-29: the library had only Kenney interface sounds; no paper, whoosh, shutter, marker, tear.)
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[4] / "tools/config"))
import s2f_config; s2f_config.load()
import datetime, json, re, shutil, subprocess, sys

from doc_common import assets

LIB = assets("sfx")[-1]   # the bundled layer ($S2F_ASSETS/sfx); entries of other ids (the ve-gen sounds) are kept
MAN = LIB / "manifest.json"
SELF = "自製（ffmpeg 合成，doc_sfx sfx_seed.py）"
# kind → ffmpeg lavfi source + filter (48 kHz mono): short, quiet-tailed, nothing tonal that could clash with the score
SYNTH = {
    "whoosh": ("anoisesrc=c=pink:d=0.7:a=0.5:r=48000",
               "highpass=f=300,lowpass=f=5000,afade=t=in:d=0.35:curve=qsin,afade=t=out:st=0.35:d=0.35:curve=qsin"),
    "shutter": ("anoisesrc=c=white:d=0.12:a=0.8:r=48000",
                "highpass=f=1800,volume='if(lt(t,0.012),1,if(between(t,0.07,0.085),0.8,0))':eval=frame"),
    "marker": ("anoisesrc=c=white:d=0.35:a=0.35:r=48000",
               "bandpass=f=3800:w=2500,tremolo=f=38:d=0.5,afade=t=in:d=0.04,afade=t=out:st=0.2:d=0.15"),
    "tear": ("anoisesrc=c=white:d=0.55:a=0.6:r=48000",
             "highpass=f=1200,tremolo=f=27:d=0.95,tremolo=f=61:d=0.6,afade=t=in:d=0.03,afade=t=out:st=0.3:d=0.25"),
    "paper": ("anoisesrc=c=pink:d=0.25:a=0.7:r=48000",
              "highpass=f=500,lowpass=f=6000,afade=t=out:st=0.01:d=0.22:curve=exp"),
}


def load():
    stamp = datetime.date.today().strftime("%Y%m%d")
    backup = LIB / f"manifest.{stamp}.json"
    if not backup.exists():
        shutil.copy(MAN, backup)
    return json.loads(MAN.read_text(encoding="utf-8"))


def save(man, entries):
    ids = {e["id"] for e in entries}
    man = [m for m in man if m["id"] not in ids] + entries
    MAN.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"✓ {len(entries)} entries → {MAN}")


def kenney(folder, pack, note):
    slug = "kenney-" + re.sub(r"[^a-z0-9]+", "-", pack.lower()).strip("-")
    entries, today = [], datetime.date.today().isoformat()
    for f in sorted(p for p in __import__("pathlib").Path(folder).rglob("*.ogg")):
        sid = f"{slug}-{f.stem.replace('_', '-')}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-ar", "48000", str(LIB / f"{sid}.wav")], check=True)
        tags = [w for w in f.stem.split("_") if not w.isdigit()]
        entries.append({"id": sid, "file": f"{sid}.wav", "query": " ".join(tags), "tags": tags, "tags_zh": [],
                        "source": f"Kenney {pack}（kenney.nl，{note}）", "license": "CC0（Kenney 官方明文可商用、免 attribution）",
                        "author": "Kenney", "source_url": f"https://kenney.nl/assets/{slug[7:]}", "downloaded_at": today})
    if not entries:
        sys.exit(f"✗ no .ogg under {folder}")
    return entries


def synth():
    entries, today = [], datetime.date.today().isoformat()
    for kind, (src, fx) in SYNTH.items():
        sid = f"self-{kind}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", src, "-af", fx + ",alimiter=limit=0.9",
                        "-ar", "48000", "-ac", "1", str(LIB / f"{sid}.wav")], check=True)
        entries.append({"id": sid, "file": f"{sid}.wav", "query": kind, "tags": [kind], "tags_zh": [], "source": SELF,
                        "license": "自製", "author": "", "source_url": "", "downloaded_at": today})
    return entries


if __name__ == "__main__":
    if sys.argv[1:2] == ["kenney"] and len(sys.argv) == 5:
        save(load(), kenney(*sys.argv[2:]))
    elif sys.argv[1:] == ["synth"]:
        save(load(), synth())
    else:
        sys.exit(__doc__)
