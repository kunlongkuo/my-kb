"""試聽版作曲：同一份譜、兩種配器，用 GeneralUser GS 離線渲染成 WAV。

用法：uv run python compose.py            # 產出 <工作資料夾>/outputs/trial-A-piano.wav、trial-B-mallet.wav（工作資料夾：$S2F_SCORE_WORK，沒設是 ./score_out）
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import random

import numpy as np
import soundfile as sf
import tinysoundfont

from paths import soundfont, work_dir

OUT = work_dir() / "outputs"
SR = 44100

# ── 譜（A 小調，每小節 4 拍）──────────────────────────────
# 和弦：根音 MIDI + 組成音（相對半音）
CHORDS = {
    "Am": (57, [0, 3, 7]), "F": (53, [0, 4, 7]), "C": (48, [0, 4, 7]),
    "G": (55, [0, 4, 7]), "E": (52, [0, 4, 7]), "Em": (52, [0, 3, 7]),
    "Dm": (50, [0, 3, 7]), "Asus": (57, [0, 5, 7]),
}
PROG = ["Am", "F", "C", "G",  "Am", "F", "C", "E",
        "F", "G", "Em", "Am",  "Dm", "F", "Asus", "Am"]
# 段落：intro 1-4 只有分解和弦＋鋪底；A 5-8 主旋律；B 9-12 主旋律與回應交替；outro 13-16 收薄
# 旋律：(小節, 拍位, 音高, 拍長, 聲部 'lead'|'reply')；音域控制在 C4(60)–E5(76)
MEL = [
    (5, 0, 69, 1.5, "lead"), (5, 1.5, 72, .5, "lead"), (5, 2, 71, 1, "lead"), (5, 3, 69, 1, "lead"),
    (6, 0, 65, 2, "lead"), (6, 2, 67, 1, "lead"), (6, 3, 69, 1, "lead"),
    (7, 0, 72, 1.5, "lead"), (7, 1.5, 74, .5, "lead"), (7, 2, 72, 1, "lead"), (7, 3, 67, 1, "lead"),
    (8, 0, 68, 3, "lead"),
    (9, 0, 72, 1, "lead"), (9, 1, 69, 1, "lead"), (9, 2, 65, 2, "lead"),
    (10, 0, 71, .5, "reply"), (10, .5, 74, .5, "reply"), (10, 1, 71, 1, "reply"), (10, 2, 67, 2, "reply"),
    (11, 0, 71, 1, "lead"), (11, 1, 67, 1, "lead"), (11, 2, 64, 2, "lead"),
    (12, 0, 72, .5, "reply"), (12, .5, 71, .5, "reply"), (12, 1, 69, 3, "reply"),
    (13, 0, 65, 1, "lead"), (13, 1, 69, 1, "lead"), (13, 2, 74, 2, "lead"),
    (14, 0, 72, 2, "reply"), (14, 2, 69, 2, "reply"),
    (15, 0, 71, 2, "lead"), (15, 2, 69, 2, "lead"),
]

# ── 配器（GM 程式號，0 起算）────────────────────────────
VERSIONS = {
    "A-piano": dict(bpm=72, lead=0, reply=46, arp=0, pad=48, bass=42,
                    shaker=False, note="piano lead, harp reply, string pad, cello bass (close to the two references)"),
    "B-mallet": dict(bpm=92, lead=12, reply=108, arp=24, pad=45, bass=32,
                     shaker=True, note="marimba lead, kalimba reply, nylon guitar arpeggios, pizzicato, wooden bass, shaker (the original scoring)"),
}
CH = dict(lead=0, reply=1, arp=2, pad=3, bass=4)


def events(v, rnd):
    """回傳 (秒, 'on'|'off', ch, key, vel) 清單。"""
    spb = 60 / v["bpm"]
    ev = []

    def note(ch, key, start_beat, beats, vel):
        t0 = start_beat * spb + rnd.uniform(0, 0.012)       # 微小人味
        vel = max(1, min(127, int(vel + rnd.randint(-6, 6))))
        ev.append((t0, "on", ch, key, vel))
        ev.append((t0 + beats * spb * 0.95, "off", ch, key, 0))

    for i, name in enumerate(PROG):
        bar, b0 = i + 1, i * 4
        root, tones = CHORDS[name]
        outro = bar >= 13
        # 分解和弦：八分音符，intro 與 outro 較輕
        arp = [root + 12 + t for t in tones] + [root + 24]
        pat = [0, 1, 2, 3, 2, 1, 2, 1] if v["bpm"] < 80 else [0, 2, 1, 3, 0, 2, 1, 2]
        for k, idx in enumerate(pat):
            if outro and bar >= 15 and k % 2:
                continue
            note(CH["arp"], arp[idx], b0 + k * .5, .5, 50 if bar <= 4 or outro else 58)
        # 鋪底：整小節長音（intro 起、outro 漸弱）
        for t in tones:
            note(CH["pad"], root + t, b0, 4, 40 - (bar - 12) * 4 if outro else 44)
        # 低音：intro 後進場
        if bar >= 5:
            note(CH["bass"], root - 12, b0, 2, 70)
            note(CH["bass"], root - 12 + tones[2], b0 + 2, 2, 60)
        # 沙鈴：A/B 段反拍
        if v["shaker"] and 5 <= bar <= 12:
            for k in range(8):
                ev.append(((b0 + k * .5) * spb, "on", 9, 70, 30 if k % 2 == 0 else 48))
    for bar, beat, key, beats, part in MEL:
        note(CH[part], key, (bar - 1) * 4 + beat, beats, 82 if part == "lead" else 74)
    # 片尾：最後和弦延長兩小節乾淨收
    end = 16 * 4
    for t in [45, 52, 57, 60, 64]:
        note(CH["pad"], t, end, 6, 40)
    note(CH["lead"], 69, end, 6, 60)
    ev.sort(key=lambda e: (e[0], e[1] == "on"))
    return ev, (end + 8) * spb


def render(name, v, seed=7):
    rnd = random.Random(seed)
    syn = tinysoundfont.Synth(samplerate=SR, gain=-6)
    sfid = syn.sfload(str(soundfont()))
    for part, ch in CH.items():
        syn.program_select(ch, sfid, 0, v[part])
    if v["shaker"]:
        syn.program_select(9, sfid, 128, 0, is_drums=True)
    ev, total = events(v, rnd)
    chunks, now = [], 0
    for t, kind, ch, key, vel in ev + [(total, "end", 0, 0, 0)]:
        n = int((t - now) * SR)
        if n > 0:
            chunks.append(np.frombuffer(syn.generate(n), dtype=np.float32).reshape(-1, 2).copy())
            now += n / SR
        if kind == "on":
            syn.noteon(ch, key, vel)
        elif kind == "off" and ch != 9:
            syn.noteoff(ch, key)
    y = np.concatenate(chunks)
    y = y / (np.abs(y).max() + 1e-9) * 0.7
    path = OUT / f"trial-{name}.wav"
    sf.write(path, y, SR)
    print(f"{path.name}  {len(y)/SR:.1f}s  {v['note']}")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, v in VERSIONS.items():
        render(name, v)
