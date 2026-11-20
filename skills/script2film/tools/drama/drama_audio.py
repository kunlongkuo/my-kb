"""drama_cut.py 的聲音處理（numpy）：讀寫 PCM、音量、人聲空檔當底噪、拼接與循環、依起點加總。

純陣列的函式（gain_to、fade、gaps、stitch、loop_to、mix_at）不碰檔案，pytest 直接測；pcm／write_wav 走 ffmpeg。
所有陣列都是 (樣本數, 2) 的 float32、取樣率 SR。
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

SR = 48000


def pcm(path, ss: float = 0.0, t: float | None = None, af: str | None = None) -> np.ndarray:
    """讀一段聲音成 (n, 2) float32、48 kHz；ss／t 秒（輸入端截），af＝額外的 ffmpeg 音訊濾鏡（例如 atempo）。"""
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}"] + (["-t", f"{t:.3f}"] if t else []) + ["-i", str(path), "-vn"]
    cmd += (["-af", af] if af else []) + ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def write_wav(path, x: np.ndarray) -> Path:
    """(n, 2) float32 → 48 kHz 立體聲 wav（32 位元浮點：加總或拉音量前峰值可能超過 1，整數格式會削波）。"""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", str(path)], input=np.ascontiguousarray(x, np.float32).tobytes(), check=True)
    return Path(path)


def rms_db(x: np.ndarray) -> float:
    """RMS 換成 dBFS（不做 K 加權，只用來把同類素材拉到相近的音量）。"""
    return float(20 * np.log10(np.sqrt(np.mean(np.square(x, dtype=np.float64))) + 1e-9)) if len(x) else -180.0


def gain_for(x: np.ndarray, target_db: float) -> float:
    """把 x 有聲的部分（任一聲道絕對值 > 1e-4 的樣本）的 RMS 拉到 target_db 要乘的倍數。整段靜音回 1。"""
    live = x[np.abs(x).max(axis=1) > 1e-4] if len(x) else x
    if not len(live):
        return 1.0
    return float(10 ** ((target_db - rms_db(live)) / 20))


def gain_to(x: np.ndarray, target_db: float) -> np.ndarray:
    return (x * gain_for(x, target_db)).astype(np.float32)


def fade(x: np.ndarray, head: float, tail: float) -> np.ndarray:
    """頭 head 秒線性淡入、尾 tail 秒線性淡出（超過長度就截到長度）。回傳新陣列。"""
    y = x.astype(np.float32, copy=True)
    a, b = min(int(head * SR), len(y)), min(int(tail * SR), len(y))
    if a > 0:
        y[:a] *= np.linspace(0, 1, a, dtype=np.float32)[:, None]
    if b > 0:
        y[len(y) - b:] *= np.linspace(1, 0, b, dtype=np.float32)[:, None]
    return y


def gaps(vocals: np.ndarray, rest: np.ndarray, pad: float = 0.35, win: float = 0.05, min_len: float = 0.4) -> list[np.ndarray]:
    """人聲音軌安靜的片段（離任何人聲 ≥ pad 秒、長度 ≥ min_len）→ 對應的 rest 片段清單。
    vocals 判斷哪裡有人聲（比全片最大窗 RMS 低 40 dB 以內算有聲），rest 是要取用的聲音（demucs 的 no_vocals，或原片聲音本身）。"""
    v = vocals.mean(axis=1) if vocals.ndim == 2 else vocals
    n = int(win * SR)
    if len(v) <= n:
        return []
    rms = np.array([np.sqrt(np.mean(v[i:i + n] ** 2)) for i in range(0, len(v) - n, n)])
    if rms.max() <= 0:
        return [rest[:len(rms) * n]]
    loud = rms > rms.max() * 10 ** (-40 / 20)
    k = int(pad / win)
    near = np.convolve(loud.astype(int), np.ones(2 * k + 1, int), "same") > 0
    out, i = [], 0
    while i < len(near):
        if not near[i]:
            j = i
            while j < len(near) and not near[j]:
                j += 1
            if (j - i) * win >= min_len:
                out.append(rest[i * n:j * n])
            i = j
        else:
            i += 1
    return out


def stitch(chunks: list[np.ndarray], xf: float = 0.1) -> np.ndarray:
    """片段依序接起來，接縫交叉淡化 xf 秒（片段太短就直接接）。"""
    m = int(xf * SR)
    out = chunks[0].copy()
    for c in chunks[1:]:
        if len(c) <= 2 * m or len(out) <= m:
            out = np.concatenate([out, c])
            continue
        w = np.linspace(0, 1, m, dtype=np.float32)[:, None]
        out = np.concatenate([out[:-m], out[-m:] * (1 - w) + c[:m] * w, c[m:]])
    return out


def loop_to(loop: np.ndarray, need: int, xf: float = 0.5) -> np.ndarray:
    """把 loop 循環到 need 個樣本，每次接回開頭交叉淡化 xf 秒（聽不出接縫）；素材比兩倍淡化還短就不淡化直接接。"""
    m = int(xf * SR)
    out = loop.copy()
    while len(out) < need:
        if len(loop) <= 2 * m or len(out) <= m:
            out = np.concatenate([out, loop])
            continue
        w = np.linspace(0, 1, m, dtype=np.float32)[:, None]
        out = np.concatenate([out[:-m], out[-m:] * (1 - w) + loop[:m] * w, loop[m:]])
    return out[:need].copy()


def mix_at(n: int, items: list[tuple[float, np.ndarray]]) -> np.ndarray:
    """(起點秒, 陣列) 依起點加總進一條 n 個樣本的軌；超出的部分截掉。"""
    out = np.zeros((n, 2), np.float32)
    for at, x in items:
        i = int(round(at * SR))
        if i >= n or not len(x):
            continue
        k = min(len(x), n - i)
        out[i:i + k] += x[:k]
    return out
