"""量化參考配樂：BPM、調性、頻譜重心、打擊比例、低中高頻能量。"""
import sys, json
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import numpy as np, librosa

KEYS = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
MAJ = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
MIN = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])

def key_of(y, sr):
    c = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    best = max(((np.corrcoef(np.roll(p, i), c)[0, 1], f"{KEYS[i]} {m}")
                for p, m in ((MAJ, 'major'), (MIN, 'minor')) for i in range(12)))
    return best[1], round(float(best[0]), 2)

def analyze(path):
    y, sr = librosa.load(path, sr=22050, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    h, p = librosa.effects.hpss(y)
    S = np.abs(librosa.stft(y)) ** 2
    f = librosa.fft_frequencies(sr=sr)
    tot = S.sum()
    band = lambda lo, hi: float(S[(f >= lo) & (f < hi)].sum() / tot)
    onset = librosa.onset.onset_detect(y=y, sr=sr)
    dur = len(y) / sr
    key, conf = key_of(h, sr)
    rms = librosa.feature.rms(y=y)[0]
    return {
        "file": path.split('/')[-1], "dur_s": round(dur, 1),
        "bpm": round(float(np.atleast_1d(tempo)[0]), 1), "key": key, "key_conf": conf,
        "centroid_hz": round(float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())),
        "perc_ratio": round(float((p**2).sum() / ((h**2).sum() + (p**2).sum())), 3),
        "onsets_per_s": round(len(onset) / dur, 2),
        "low<250": round(band(0, 250), 3), "mid250-2k": round(band(250, 2000), 3),
        "high>2k": round(band(2000, sr / 2), 3),
        "rms_db": round(float(20 * np.log10(rms.mean() + 1e-9)), 1),
        "dyn_range_db": round(float(20 * np.log10(np.percentile(rms, 95) / (np.percentile(rms, 10) + 1e-9))), 1),
    }

if __name__ == "__main__":
    print(json.dumps([analyze(p) for p in sys.argv[1:]], ensure_ascii=False, indent=1))
