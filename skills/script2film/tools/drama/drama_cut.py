"""演戲版（無旁白、對嘴對白）的組裝：一份時間軸 cut.json → 成片或 Concat 專案；也能把使用者在 Concat 的剪法讀回來。

用法（倉庫根目錄）：
  python3 tools/drama/drama_cut.py check  <cut.json>              # 收片後先跑：對白有沒有被截（語音辨識）、畫面燒字（macOS Vision）、缺檔
  python3 tools/drama/drama_cut.py render <cut.json>              # 不靠 Concat 直接出片：<cut 所在資料夾>/<name>.mp4＋.srt（已存在就加 _v2…）
  python3 tools/drama/drama_cut.py concat <cut.json> [--export] [--no-check <項目>:<原因>]   # Concat 專案（走 MCP 不開視窗）；--export 順便匯出成片並體檢
  python3 tools/drama/drama_cut.py pull   <cut.json> <Concat 專案資料夾>   # 讀回剪法 → <cut>_pulled.json＋改動報告

格式見 dramalib.py 開頭與 README.md。對白語音辨識用本機 whisper.cpp（設定檔或環境變數 S2F_WHISPER_CPP_MODEL）。
"""
from __future__ import annotations

import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()  # noqa: E401,E402

import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import dramalib as dl  # noqa: E402
import drama_audio as da  # noqa: E402

GRADES = {"old_photo": "colorchannelmixer=rr=1.0:rg=0.08:rb=0.0:gr=0.04:gg=0.94:gb=0.0:br=0.02:bg=0.06:bb=0.80,"
                       "noise=alls=7:allf=t,vignette=PI/5"}
GRADE_NAMES = {"old_photo": "老照片"}
SUB_STYLE = {"size": 50, "stroke": 4, "bottom": 130}   # render 的字幕：白字、黑描邊、字高 50、上緣在底部往上 130 像素


def sh(*cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def probe_dur(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


def has_audio(p: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
                        str(p)], capture_output=True, text=True)
    return bool(r.stdout.strip())


def free_path(folder: Path, name: str, exts: tuple[str, ...]) -> str:
    """<name>、<name>_v2、<name>_v3…裡第一個所有副檔名都還沒有檔的名字（不覆蓋）。"""
    k, cand = 2, name
    while any((folder / f"{cand}{e}").exists() for e in exts):
        cand, k = f"{name}_v{k}", k + 1
    return cand


class Cut:
    def __init__(self, path: str):
        self.path = Path(path).resolve()
        self.base = self.path.parent
        try:
            self.cfg = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            sys.exit(f"✗ {self.path}: no such file")
        except ValueError as e:
            sys.exit(f"✗ {self.path}: not valid JSON ({e})")
        try:
            dl.check_cfg(self.cfg)
        except ValueError as e:
            sys.exit(f"✗ {self.path.name}: {e}")
        self.shots = self.cfg["shots"]
        self.fps = int(self.cfg.get("fps", 30))
        self.work = self.base / f".{self.path.stem}"
        self.work.mkdir(exist_ok=True)
        self._sep: dict[str, Path] = {}
        self._gain: dict[str, float] = {}

    def p(self, rel: str) -> Path:
        return (self.base / rel).resolve()

    def font(self) -> Path:
        if self.cfg.get("font"):
            return self.p(self.cfg["font"])
        assets = Path(os.environ["S2F_ASSETS"]) if os.environ.get("S2F_ASSETS") else REPO / "assets"
        return assets / "fonts/NotoSerifTC-Variable.ttf"

    def sfx(self, name: str) -> Path:
        d = self.p(self.cfg.get("sfx_dir", "sfx"))
        for ext in (".mp3", ".wav"):
            if (d / f"{name}{ext}").exists():
                return d / f"{name}{ext}"
        sys.exit(f"✗ missing sound effect {name} ({d})")

    # ---- 對白的聲音來源：原片或 demucs 人聲 ----
    def stem(self) -> str:
        return (self.cfg.get("dialogue") or {}).get("stem", "original")

    def sep_root(self) -> Path:
        return self.p(self.cfg["sep_dir"]) if self.cfg.get("sep_dir") else self.work / "sep"

    @staticmethod
    def sep_keys(src: str) -> list[str]:
        """快取資料夾名的候選：來源路徑把 / 換成 _、去掉 .mp4（略過 . 與 ..）；再依序去掉開頭幾層，
        讓 cut.json 寫成 ../runs/r3/clips/a.mp4 也找得到以 r3/clips/a.mp4 為名的既有快取。第一個是新拆時用的名字。"""
        parts = [c for c in Path(src).parts if c not in (".", "..", "/")]
        keys = []
        for i in range(len(parts)):
            k = "_".join(parts[i:])
            keys.append(k[:-4] if k.endswith(".mp4") else k)
        return keys

    def separate(self, srcs: list[str]):
        """demucs 兩軌（vocals／no_vocals）；已經有快取就不重跑。"""
        root = self.sep_root() / "htdemucs"
        todo, hit = [], 0
        for s in dict.fromkeys(srcs):
            found = next((root / k for k in self.sep_keys(s) if (root / k / "vocals.wav").exists()), None)
            if found:
                self._sep[s] = found
                hit += 1
                continue
            w = self.work / "wav" / f"{self.sep_keys(s)[0]}.wav"
            w.parent.mkdir(parents=True, exist_ok=True)
            sh("ffmpeg", "-v", "error", "-y", "-i", self.p(s), "-vn", "-ac", "2", "-ar", da.SR, w)
            todo.append((s, w))
        if todo:
            if not shutil.which("demucs"):
                sys.exit("✗ demucs not found (needed only when dialogue.stem is vocals): python3 -m pip install demucs; or set dialogue.stem to original")
            sh("demucs", "--two-stems", "vocals", "-n", "htdemucs", "-o", self.sep_root(), *[w for _, w in todo])
            for s, w in todo:
                self._sep[s] = root / w.stem
        print(f"demucs: {hit} from the cache, {len(todo)} newly separated ({root})")

    def dialogue_file(self, src: str) -> Path:
        return self._sep[src] / "vocals.wav" if self.stem() == "vocals" else self.p(src)

    def bed_sources(self, src: str):
        """（判斷人聲用的聲音, 取用的聲音）：vocals 模式是 demucs 的人聲與 no_vocals，original 模式兩者都是原片聲音。"""
        if self.stem() == "vocals":
            return da.pcm(self._sep[src] / "vocals.wav"), da.pcm(self._sep[src] / "no_vocals.wav")
        x = da.pcm(self.p(src))
        return x, x

    def dialogue(self, s: dict, length: float):
        """一鏡的對白：從 in 取 length×speed 秒（倍速時 atempo），音量照整支來源算的倍數，頭尾各淡 20 毫秒。"""
        f, sp = self.dialogue_file(s["src"]), float(s.get("speed", 1.0))
        db = (self.cfg.get("dialogue") or {}).get("db")
        if db is not None and str(f) not in self._gain:
            self._gain[str(f)] = da.gain_for(da.pcm(f), float(db))
        x = da.pcm(f, float(s.get("in", 0)), length * sp, af=f"atempo={sp}" if abs(sp - 1) > 1e-9 else None)
        return da.fade(x * self._gain.get(str(f), 1.0), 0.02, 0.02)


# ---- 畫面段 ----
def color_arg(c: str) -> str:
    return "0x" + c[1:] if c.startswith("#") else c


def text_png(cut: Cut, name: str, text: str, size: int) -> Path:
    """字卡文字：Pillow 畫成透明 PNG 再 overlay（ffmpeg 不一定有 drawtext）。"""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(cut.font()), size)
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
    d.text(((1920 - (x1 - x0)) // 2 - x0, (1080 - (y1 - y0)) // 2 - y0), text, font=f, fill=(232, 220, 196, 255))
    out = cut.work / f"{name}.png"
    img.save(out)
    return out


def lines_png(cut: Cut, name: str, lines: list[dict], shadow: bool) -> Path:
    """多行白字（各行水平置中、y＝上緣像素、可各自指定字型）畫成透明 PNG；shadow＝疊在畫面上時加兩層陰影。"""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for ln in lines:
        f = ImageFont.truetype(str(cut.p(ln["font"]) if ln.get("font") else cut.font()), int(ln["size"]))
        x, y = (1920 - d.textlength(ln["text"], font=f)) / 2, float(ln["y"])
        if shadow:
            for dx, dy in ((3, 3), (2, 2)):
                d.text((x + dx, y + dy), ln["text"], font=f, fill=(0, 0, 0, 150))
        d.text((x, y), ln["text"], font=f, fill=(255, 255, 255, 255))
    out = cut.work / f"{name}.png"
    img.save(out)
    return out


def encode(*args, frames: int, out: Path):
    sh("ffmpeg", "-v", "error", "-y", *args, "-frames:v", frames, "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out)


def card_clip(cut: Cut, s: dict, out: Path, frames: int):
    dur = frames / cut.fps
    card = s["card"]
    if isinstance(card, dict):
        png, bg = lines_png(cut, f"{s['id']}_card", card["lines"], shadow=False), color_arg(card.get("bg", "#000000"))
    else:
        png, bg = text_png(cut, f"{s['id']}_card", card, 64), "0x15110d"
    fc = (f"[1:v]format=rgba,fade=in:st=0:d=0.6:alpha=1,fade=out:st={max(dur - 0.6, 0):.3f}:d=0.6:alpha=1[t];"
          f"[0:v][t]overlay=0:0,format=yuv420p[v]")
    encode("-f", "lavfi", "-i", f"color=c={bg}:s=1920x1080:r={cut.fps}:d={dur + 1:.3f}",
           "-loop", "1", "-framerate", cut.fps, "-t", f"{dur + 1:.3f}", "-i", png, "-filter_complex", fc, "-map", "[v]",
           frames=frames, out=out)


def shot_clip(cut: Cut, s: dict, out: Path, frames: int, start: float):
    """一鏡無聲畫面：入點、長度、翻轉／裁切／放大、插入鏡、片名（字幕與聲音另外處理）。
    -t 一定放在 -i 前面（輸入端截）：放在後面會連 tpad 之類的延長一起截掉。長度用 -frames:v 卡格數。"""
    dur, speed = float(s["dur"]), float(s.get("speed", 1.0))
    pics = dl.pics_of(s)
    inputs, graph = [], []
    if pics:
        counts = dl.frame_counts([p["dur"] for p in pics], cut.fps, start)
        for k, (p, n) in enumerate(zip(pics, counts)):
            inputs += ["-ss", p["in"], "-t", f"{p['dur'] + 0.5:.3f}", "-i", cut.p(p["src"])]
            graph.append(dl.shot_filter({**p, "id": f"{s['id']} pics {k}"}, cut.fps, inp=f"{k}:v", out=f"s{k}", tag=f"q{k}")
                         + f";[s{k}]trim=end_frame={n},setpts=PTS-STARTPTS[c{k}]")
        graph.append("".join(f"[c{k}]" for k in range(len(pics))) + f"concat=n={len(pics)}:v=1:a=0[v0]")
    else:
        inputs += ["-ss", s.get("in", 0), "-t", f"{dur * speed + 0.5:.3f}", "-i", cut.p(s["src"])]
        graph.append(dl.shot_filter(s, cut.fps, out="v0"))
    last = "v0"
    t = s.get("title")
    if t:
        k = len(pics) or 1
        png = lines_png(cut, f"{s['id']}_title", t["lines"], shadow=True)
        a, b = float(t.get("from", 0)), float(t.get("to", dur))
        inputs += ["-loop", "1", "-framerate", cut.fps, "-t", f"{dur + 1:.3f}", "-i", png]
        graph.append(f"[{k}:v]format=rgba,fade=in:st={a:g}:d=0.8:alpha=1,fade=out:st={max(b - 0.8, a):g}:d=0.8:alpha=1[tt];"
                     f"[v0][tt]overlay=0:0[v1]")
        last = "v1"
    graph.append(f"[{last}]format=yuv420p[v]")
    encode(*inputs, "-an", "-filter_complex", ";".join(graph), "-map", "[v]", frames=frames, out=out)


def build_clips(cut: Cut, folder: Path) -> tuple[list[Path], list[float]]:
    """每鏡一支畫面檔；格數照設定的累計起訖點取整（frame_counts），長短不會一鏡一鏡累積。"""
    folder.mkdir(parents=True, exist_ok=True)
    counts = dl.frame_counts([float(s["dur"]) for s in cut.shots], cut.fps)
    clips, durs = [], []
    for i, (s, n, st) in enumerate(zip(cut.shots, counts, dl.offsets(cut.shots))):
        out = folder / f"{i:02d}_{s['id']}.mp4"
        if "card" in s:
            card_clip(cut, s, out, n)
        else:
            shot_clip(cut, s, out, n, st)
        clips.append(out)
        durs.append(probe_dur(out))
    return clips, durs


# ---- 共用素材：畫面段＋各軌聲音＋字幕 ----
def scene_bed(cut: Cut, name: str, sc: dict, length: float) -> "da.np.ndarray":
    if sc["bed"] == "auto":
        srcs = list(dict.fromkeys(s["src"] for s in cut.shots if s.get("scene") == name and s.get("speaker")))
        chunks = []
        for src in srcs:
            v, rest = cut.bed_sources(src)
            chunks += da.gaps(v, rest)
        if not chunks:
            sys.exit(f"✗ the source clips of scene \"{name}\" have no gap without voices (≥0.4s, at least 0.35s from speech); "
                     f"set scenes.{name}.bed to the path of a room tone file")
        loop = da.stitch(chunks)
    else:
        loop = da.pcm(cut.p(sc["bed"]))
    print(f"room tone {name}: {len(loop) / da.SR:.1f}s of material laid over {length:.1f}s")
    loop = da.gain_to(loop, float(sc.get("db", -33)))
    out = da.loop_to(loop, int(round(length * da.SR)))
    return da.fade(out, 0.03, float(sc.get("fade_out", 0.03)))


def parts(cut: Cut, folder: Path) -> dict:
    """render 與 Concat 共用的素材：每鏡一段無聲畫面（已裁切、片名與字卡已畫進去、不燒字幕）、對白依角色、音效（音量先套進檔案）、
    各場底噪、配樂、字幕。檔名就是讀回時對鏡號的依據：NN_<鏡>.mp4、NN_<鏡>_<角色>.wav、sfx_<序號>_<名>.wav。"""
    clips, durs = build_clips(cut, folder)
    starts = dl.offsets(cut.shots, durs)
    t = dl.total(cut.shots, durs)
    audios = []
    talk = [s for s in cut.shots if s.get("speaker") and has_audio(cut.p(s["src"]))]
    auto_src = [s["src"] for s in cut.shots if s.get("speaker") and s.get("scene")
                and (cut.cfg.get("scenes") or {}).get(s["scene"], {}).get("bed") == "auto"]
    if cut.stem() == "vocals":
        cut.separate([s["src"] for s in talk] + auto_src)
    for i, (s, st, d) in enumerate(zip(cut.shots, starts, durs)):
        if s in talk:
            a = folder / f"{i:02d}_{s['id']}_{s['speaker']}.wav"
            # 尾端少 1ms：相鄰段首尾相接時秒→微秒的四捨五入會讓兩段重疊，剪輯軟體會拒收
            da.write_wav(a, cut.dialogue(s, d - 0.001))
            audios.append({"path": str(a), "start_us": round(st * 1e6), "track": f"對白-{s['speaker']}"})
    cues = dl.sfx_cues(cut.shots, durs)
    files = []
    for c in cues:  # 音量先套進檔案
        a = folder / f"sfx_{c['k']:02d}_{c['name']}.wav"
        sh("ffmpeg", "-v", "error", "-y", "-i", cut.sfx(c["name"]), "-af", f"volume={c['db']}dB",
           "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", a)
        files.append(a)
    for c, a, lane in zip(cues, files, dl.lanes([(c["at"], probe_dur(a)) for c, a in zip(cues, files)])):
        audios.append({"path": str(a), "start_us": round(c["at"] * 1e6), "track": f"音效{lane + 1}"})
    rt = cut.cfg.get("roomtone")
    if rt:
        bed = folder / "roomtone_bed.wav"
        sh("ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", cut.sfx(rt["name"]), "-t", f"{t:.3f}",
           "-af", f"volume={rt.get('db', -26)}dB", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", bed)
        audios.append({"path": str(bed), "start_us": 0, "track": "房間底噪"})
    spans = dl.scene_spans(cut.shots, durs)
    for name, sc in (cut.cfg.get("scenes") or {}).items():
        if name not in spans:
            continue
        a, b = spans[name]
        path = folder / f"bed_{name}.wav"
        da.write_wav(path, scene_bed(cut, name, sc, b - a))
        audios.append({"path": str(path), "start_us": round(a * 1e6), "track": f"底噪-{name}"})
    mus = cut.cfg.get("music")
    if mus:
        ids = [s["id"] for s in cut.shots]
        stop = starts[ids.index(mus["stop_at"])] if mus.get("stop_at") else t
        x = da.gain_to(da.pcm(cut.p(mus["file"]), 0, stop), float(mus.get("db", -31)))[:int(stop * da.SR)]
        path = folder / "music.wav"
        da.write_wav(path, da.fade(x, 0.05, 0.03))
        audios.append({"path": str(path), "start_us": 0, "track": "配樂"})
    return {"clips": clips, "durs": durs, "starts": starts, "total": t, "audios": audios, "spans": spans,
            "subs": dl.subtitles(cut.shots, durs)}


# ---- render：不靠 Concat 直接出片 ----
def bus_of(track: str) -> str:
    if track.startswith("對白"):
        return "dialogue"
    if track.startswith("音效"):
        return "sfx"
    if track == "配樂":
        return "music"
    return "bed"


def sub_png(cut: Cut, text: str, path: Path):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(str(cut.font()), SUB_STYLE["size"])
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x, y = (1920 - d.textlength(text, font=f)) / 2, 1080 - SUB_STYLE["bottom"]
    d.text((x, y), text, font=f, fill=(255, 255, 255, 255), stroke_width=SUB_STYLE["stroke"], stroke_fill=(0, 0, 0, 220))
    im.save(path)


def render(cut: Cut):
    """parts() 的產物直接合成：畫面段 ffmpeg concat；所有聲音依起點加總（各類另存 bus_*.wav）後 loudnorm；
    字幕畫成透明 PNG 以 overlay enable 疊上（不需要 drawtext／subtitles 濾鏡）。"""
    folder = cut.work / "render"
    P = parts(cut, folder)
    name = free_path(cut.base, cut.cfg["name"], (".mp4", ".srt"))
    out, srt_path = cut.base / f"{name}.mp4", cut.base / f"{name}.srt"
    lst = folder / "clips.txt"
    lst.write_text("".join(f"file '{c}'\n" for c in P["clips"]), encoding="utf-8")
    video = folder / "video.mp4"
    sh("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", 0, "-i", lst, "-c", "copy", video)

    n = int(round(P["total"] * da.SR))
    buses: dict[str, list] = {}
    for a in P["audios"]:
        buses.setdefault(bus_of(a["track"]), []).append((a["start_us"] / 1e6, da.pcm(a["path"])))
    mix = da.np.zeros((n, 2), da.np.float32)
    for bus, items in buses.items():
        x = da.mix_at(n, items)
        da.write_wav(folder / f"bus_{bus}.wav", x)
        mix += x
    raw, norm = folder / "mix_raw.wav", folder / "mix.wav"
    da.write_wav(raw, mix)
    sh("ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", da.SR, norm)

    inputs, chain, prev = [], [], "0:v"
    for i, (a, b, text) in enumerate(P["subs"]):
        p = folder / f"sub{i:02d}.png"
        sub_png(cut, text, p)
        inputs += ["-i", str(p)]
        chain.append(f"[{prev}][{i + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[s{i}]")
        prev = f"s{i}"
    crf = os.environ.get("S2F_EXPORT_CRF", "")
    crf = crf if crf.isdigit() and 16 <= int(crf) <= 32 else "24"
    if chain:
        fc = folder / "subs_filter.txt"
        fc.write_text(";\n".join(chain), encoding="utf-8")
        vargs = ["-/filter_complex", str(fc), "-map", f"[{prev}]", "-c:v", "libx264", "-crf", crf, "-pix_fmt", "yuv420p"]
    else:
        vargs = ["-map", "0:v", "-c:v", "copy"]
    sh("ffmpeg", "-v", "error", "-y", "-i", video, "-i", norm, *inputs, *vargs, "-map", "1:a",
       "-c:a", "aac", "-b:a", "192k", "-shortest", out)
    srt_path.write_text(dl.srt(P["subs"]), encoding="utf-8")
    (folder / "timeline.json").write_text(json.dumps(
        {"total": round(P["total"], 3), "scenes": {k: [round(a, 3), round(b, 3)] for k, (a, b) in P["spans"].items()},
         "shots": [{"id": s["id"], "at": round(st, 3), "dur": round(d, 3)} for s, st, d in zip(cut.shots, P["starts"], P["durs"])]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"film: {out} ({probe_dur(out):.2f}s, {len(P['clips'])} shots, {len(P['subs'])} subtitles)\nsubtitles: {srt_path}\n"
          f"intermediate files: {folder} (bus_*.wav = each kind of sound, timeline.json = where each shot starts)")
    return out


# ---- concat ----
SUB_BAND = {"maxWidth": 1200 / 1920, "maxHeight": 120 / 1080, "offsetY": (1000 - 540) / 1080}  # 底部 y 940–1060 的黑條


def media_item(path: str) -> dict:
    """Concat addMedia 要的素材描述。"""
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                                  capture_output=True, text=True, check=True).stdout)
    v = next((x for x in j["streams"] if x["codec_type"] == "video"), None)
    a = next((x for x in j["streams"] if x["codec_type"] == "audio"), None)
    m = {"path": path, "name": os.path.basename(path), "kind": "video" if v else "audio", "hasAudio": bool(a),
         "duration": float(j["format"]["duration"])}
    if v:
        m.update(width=v["width"], height=v["height"], frameRateFraction=v["r_frame_rate"], videoCodec=v["codec_name"])
    if a:
        m.update(audioCodec=a["codec_name"], audioTracks=[{"index": a["index"], "channels": a["channels"],
                                                           "sampleRate": int(a["sample_rate"]), "codec": a["codec_name"]}])
    return m


def concat_mcp():
    sys.path.insert(0, str(REPO / "tools/concat"))
    import plan2concat_mcp as pm
    return pm


def track_order(t: str):
    """對白在前，音效其次，底噪、配樂在最後。"""
    return (not t.startswith("對白"), t.startswith("房間") or t.startswith("底噪"), t == "配樂", t)


def concat(cut: Cut, export: bool, no_check=()):
    """Concat 專案（走 concat --mcp，不用開視窗）：主畫面一軌（片名與字卡已畫進畫面段）、字幕在最上層、
    對白／音效／各場底噪／配樂各自一軌。專案放 <cut 所在資料夾>/concat/<名稱>，同名已存在就加 _v2…；
    --export 時匯出、兩段式 loudnorm 到 -14 LUFS，設了 grade 再另出一版調色。"""
    pm = concat_mcp()
    P = parts(cut, cut.work / "concat_media")
    loc = cut.base / "concat"
    loc.mkdir(exist_ok=True)
    name, k = cut.cfg["name"], 2
    while (loc / name).exists():
        name, k = f"{cut.cfg['name']}_v{k}", k + 1
    proj = str(loc / name)
    fam = "Noto Serif TC"
    tracks = ["字幕", "畫面"] + sorted({a["track"] for a in P["audios"]}, key=track_order)
    c = pm.MCP()
    c.tool("project_create", location=str(loc), name=name, video={"width": 1920, "height": 1080, "rateNum": cut.fps, "rateDen": 1})
    batch = lambda cmds: c.tool("edit_apply", path=proj, command={"op": "batch", "commands": cmds})  # noqa: E731
    media = [str(x) for x in P["clips"]] + sorted({a["path"] for a in P["audios"]})
    batch([{"op": "addFont", "family": fam, "path": str(cut.font())}]
          + [{"op": "addMedia", "item": media_item(m)} for m in media]
          + [{"op": "addTrack", "bottom": True} for _ in range(max(0, len(tracks) - 4))])
    tl = c.tool("timeline_read", path=proj)
    mid = {m["path"]: m["id"] for m in tl["media"]}
    lanes = [t["id"] for t in sorted(tl["timeline"]["tracks"], key=lambda t: -t["index"])]  # index 0 在最下面
    lane = dict(zip(tracks, lanes))
    cmds = [{"op": "addClip", "mediaId": mid[str(cl)], "trackId": lane["畫面"], "start": round(st, 4)}
            for cl, st in zip(P["clips"], P["starts"])]
    cmds += [{"op": "addClip", "mediaId": mid[a["path"]], "trackId": lane[a["track"]], "start": round(a["start_us"] / 1e6, 4)}
             for a in P["audios"]]
    for a0, b0, text in P["subs"]:
        cmds.append({"op": "addTextClip", "trackId": lane["字幕"], "start": round(a0, 4), "duration": round(b0 - a0, 4),
                     "offsetY": SUB_BAND["offsetY"],
                     "style": {"content": text, "fontFamily": fam, "fontWeight": 400, "fontSize": 0.032, "color": "#ffffff",
                               "shadow": False, "align": "center", "background": "#000000", "backgroundRadius": 0,  # 不帶 alpha＝全不透明；半透明在匯出時會讓燒字透出來
                               "maxWidth": SUB_BAND["maxWidth"], "maxHeight": SUB_BAND["maxHeight"]}})
    batch(cmds)
    c.tool("project_save", path=proj)
    tl = c.tool("timeline_read", path=proj)
    print(f"Concat project: {proj}\n{len(tl['timeline']['clips'])} clips, {tl['timeline']['duration']:.1f}s (set to {P['total']:.1f})")
    if export:
        out = cut.base / f"{name}_原色.mp4"  # 跟專案同版本號：_v2 專案不覆蓋 v1 的成片

        def post(path):   # 交付檔：設了 grade 是調色版，否則是原色版；體檢跑在交付檔上
            pm.loudnorm(path)
            pm.trim_silent_tail(path)
            print(path)
            if not cut.cfg.get("grade"):
                return path
            g = cut.base / f"{name}_{GRADE_NAMES.get(cut.cfg['grade'], cut.cfg['grade'])}.mp4"
            sh("ffmpeg", "-v", "error", "-y", "-i", path, "-vf", GRADES[cut.cfg["grade"]], "-c:v", "libx264", "-crf", "18",
               "-c:a", "copy", g)
            print(g)
            return str(g)
        try:
            pm.concat_export(c, proj, out, post=post, ep=cut.base, no_check=no_check,
                             inputs=[cut.path, *P["clips"], *sorted({a["path"] for a in P["audios"]})])
        except pm.FilmCheckFailed:
            c.p.stdin.close()
            sys.exit(1)
    c.p.stdin.close()
    c.p.wait(timeout=30)


# ---- pull ----
def pull(cut: Cut, source: str):
    """source：Concat 專案資料夾（路徑）。"""
    if not Path(source).is_dir():
        sys.exit(f"✗ pull needs a Concat project folder: {source}")
    pm = concat_mcp()
    c = pm.MCP()
    proj = str(Path(source).resolve())
    c.tool("project_open", path=proj)
    tl = c.tool("timeline_read", path=proj)
    c.p.stdin.close()
    c.p.wait(timeout=30)
    info, names, full = dl.concat_as_draft(tl)
    new, report = dl.pull(cut.cfg, info, names, full)
    out = cut.path.with_name(f"{cut.path.stem}_pulled.json")
    out.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(report) or "(no changes)")
    print(f"→ {out} ({dl.total(new['shots']):.1f}s; once checked, rename it to replace {cut.path.name})")


# ---- check ----
def asr_words(paths: list[Path], lang: str) -> dict:
    sys.path.insert(0, str(REPO / "skills/ve-director/doc/scripts"))
    from doc_common import local_asr
    r = local_asr(paths, lang, words=True)
    if r is None:
        sys.exit("✗ no local speech recognition: set S2F_WHISPER_CPP_MODEL (python3 tools/config/s2f_config.py --show shows the current values)")
    return {Path(k): [w for seg in v["segments"] for w in seg.get("words", [])] for k, v in r.items()}


def ocr(images: list[Path]) -> dict[str, list[str]]:
    """macOS Vision 文字辨識（pyobjc-framework-Vision）。回傳每張圖辨識到的文字。沒裝或非 macOS 回空，品檢照跑、只是不查燒字。"""
    try:
        import Vision
        from Foundation import NSURL
    except ImportError:
        print("  (pyobjc-framework-Vision not installed, skipping the burned-in text check: python3 -m pip install --user pyobjc-framework-Vision)")
        return {}
    out = {}
    for img in images:
        texts = []
        req = Vision.VNRecognizeTextRequest.alloc().init()
        req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        req.setRecognitionLanguages_(["zh-Hant", "zh-Hans", "en-US"])
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(str(img)), None)
        ok, _err = handler.performRequests_error_([req], None)
        for o in (req.results() or []) if ok else []:
            c = o.topCandidates_(1)
            if c and c[0].confidence() >= 0.2:  # 生成影片燒的多是亂碼字，信心常只有 0.3 左右
                texts.append(str(c[0].string()))
        out[str(img)] = texts
    return out


def check(cut: Cut):
    tmp = Path(tempfile.mkdtemp(prefix="drama_check_", dir=cut.work))
    bad = 0
    srcs = [s["src"] for s in cut.shots if "src" in s] + [p["src"] for s in cut.shots for p in dl.pics_of(s)]
    for name, sc in (cut.cfg.get("scenes") or {}).items():
        if sc["bed"] != "auto":
            srcs.append(sc["bed"])
    if cut.cfg.get("music"):
        srcs.append(cut.cfg["music"]["file"])
    missing = sorted({x for x in srcs if not cut.p(x).exists()})
    if missing:
        sys.exit("✗ missing files: " + ", ".join(missing))
    talk = [s for s in cut.shots if s.get("speaker")]
    span = {s["id"]: float(s["dur"]) * float(s.get("speed", 1.0)) for s in cut.shots}  # 來源要取的秒數
    wavs = []
    for s in talk:
        w = tmp / f"{s['id']}.wav"
        sh("ffmpeg", "-v", "error", "-y", "-ss", s.get("in", 0), "-t", span[s["id"]], "-i", cut.p(s["src"]), "-vn", "-ar", "16000", w)
        wavs.append(w)
    words = asr_words(wavs, cut.cfg.get("lang", "zh")) if wavs else {}
    print("== dialogue")
    for s, w in zip(talk, wavs):
        line = " ".join(x["text"] for x in dl.subs_of(s))
        st = dl.line_status(line, words.get(w, []), span[s["id"]])
        heard = "".join(x["word"] for x in words.get(w, []))
        mark = "✓" if st["ok"] else "✗"
        bad += not st["ok"]
        extra = f" | speech starts at {st['lead']}s, {st['tail']}s blank at the end (an edit can trim the blanks)" if "lead" in st else ""
        print(f"  {mark} {s['id']} \"{heard.strip()}\" {st['got']}/{st['want']}{extra} {st['reason']}")
    print("== burned-in text (3 frames from each picture segment; the subtitle bar covers y 940–1060 at the bottom, text anywhere else needs handling)")
    frames = []
    for s in cut.shots:
        if "src" not in s:
            continue
        segs = dl.pics_of(s) or [{"src": s["src"], "in": float(s.get("in", 0)), "dur": span[s["id"]]}]
        for j, g in enumerate(segs):
            for k, f in enumerate((0.2, 0.5, 0.8)):
                img = tmp / f"{s['id']}_{j}_{k}.jpg"
                sh("ffmpeg", "-v", "error", "-y", "-ss", g["in"] + g["dur"] * f, "-i", cut.p(g["src"]),
                   "-frames:v", "1", "-vf", "scale=1920:1080", img)
                frames.append((s["id"], img))
    found = ocr([f for _, f in frames])
    hits: dict[str, set] = {}
    for sid, img in frames:
        for t in found.get(str(img), []):
            if len(dl.CJK.findall(t)) >= 2:
                hits.setdefault(sid, set()).add(t)
    for sid, ts in hits.items():
        print(f"  ⚠ {sid}: {', '.join(sorted(ts))}")
    if not hits:
        print("  ✓ no burned-in text seen" if found else "  (no text recognition done)")
    print("== length")
    for s in cut.shots:
        segs = dl.pics_of(s) or ([{"src": s["src"], "in": float(s.get("in", 0)), "dur": span[s["id"]]}] if "src" in s else [])
        if "src" in s and dl.pics_of(s):
            segs.append({"src": s["src"], "in": float(s.get("in", 0)), "dur": span[s["id"]]})   # 聲音整段取自 src
        for g in segs:
            have = probe_dur(cut.p(g["src"])) - g["in"]
            if have + 0.05 < g["dur"]:
                bad += 1
                print(f"  ✗ {s['id']} ({g['src']}): needs {g['dur']:.2f}s, the source has only {have:.2f}s left")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"result: {'✓ passed' if not bad else f'✗ {bad} to fix'} (burned-in text is only a reminder)")
    return bad


USAGE = """Assemble the acted version (no narration, lip-synced dialogue): one timeline cut.json → a film or a Concat project;
it can also read back how you cut it in Concat.

Usage (from the repository root):
  python3 tools/drama/drama_cut.py check  <cut.json>              # run first after the clips arrive: dialogue cut off (speech recognition), burned-in text (macOS Vision), missing files
  python3 tools/drama/drama_cut.py render <cut.json>              # film without Concat: <cut's folder>/<name>.mp4 + .srt (adds _v2… if it exists)
  python3 tools/drama/drama_cut.py concat <cut.json> [--export] [--no-check ITEM:REASON]   # Concat project (over MCP, no window); --export also exports and checks the film
  python3 tools/drama/drama_cut.py pull   <cut.json> <Concat project folder>   # read the cut back → <cut>_pulled.json + a report of the changes

Format: the top of dramalib.py and README.md. Dialogue recognition uses local whisper.cpp (S2F_WHISPER_CPP_MODEL, in the settings file or the environment)."""


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("check", "render", "pull", "concat"):
        sys.exit(USAGE)
    cut = Cut(sys.argv[2])
    if sys.argv[1] == "concat":
        import argparse
        ap = argparse.ArgumentParser(prog="drama_cut.py concat")
        concat_mcp().add_no_check(ap)
        known, _ = ap.parse_known_args(sys.argv[3:])
        return concat(cut, export="--export" in sys.argv, no_check=concat_mcp().parse_no_check(ap, known.no_check))
    if sys.argv[1] == "render":
        return render(cut)
    if sys.argv[1] == "pull":
        if len(sys.argv) < 4:
            sys.exit("pull needs a Concat project folder")
        pull(cut, sys.argv[3])
    else:
        sys.exit(1 if check(cut) else 0)


if __name__ == "__main__":
    main()
