import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import drama_audio as da  # noqa: E402

SR = da.SR


def tone(sec, amp=0.5, f=220.0):
    t = np.arange(int(sec * SR)) / SR
    x = (amp * np.sin(2 * np.pi * f * t)).astype(np.float32)
    return np.stack([x, x], axis=1)


def test_gain_to_ignores_silence():
    x = np.concatenate([tone(1.0, 0.1), np.zeros((SR, 2), np.float32)])
    y = da.gain_to(x, -18)
    assert da.rms_db(y[:SR]) == pytest.approx(-18, abs=0.05)   # 只量有聲的那一半
    assert np.all(y[SR:] == 0)
    z = np.zeros((100, 2), np.float32)
    assert da.gain_for(z, -18) == 1.0


def test_fade_head_and_tail():
    x = np.ones((SR, 2), np.float32)
    y = da.fade(x, 0.02, 0.5)
    assert y[0, 0] == 0 and y[int(0.02 * SR), 0] == 1 and y[-1, 0] == 0
    assert y[SR // 2 - 10, 0] == 1 and 0 < y[-SR // 4, 0] < 1
    assert np.all(x == 1)   # 不改原陣列


def test_gaps_returns_rest_where_voice_is_quiet():
    voice = np.concatenate([tone(1.0), np.zeros((2 * SR, 2), np.float32), tone(1.0)])
    rest = np.full_like(voice, 0.01)
    rest[SR:3 * SR] = 0.02   # 人聲空檔裡的底噪做記號
    g = da.gaps(voice, rest)
    assert len(g) == 1
    sec = len(g[0]) / SR
    assert 1.1 <= sec <= 1.4   # 2 秒空檔前後各讓 0.35 秒
    assert np.allclose(g[0], 0.02)
    assert da.gaps(tone(2.0), tone(2.0)) == []   # 整段都在講話：沒有空檔


def test_stitch_crossfades_seams():
    a, b = np.ones((SR, 2), np.float32), np.zeros((SR, 2), np.float32)
    out = da.stitch([a, b], xf=0.1)
    assert len(out) == 2 * SR - int(0.1 * SR)
    mid = SR - int(0.05 * SR)
    assert 0.3 < out[mid, 0] < 0.7


def test_loop_to_reaches_length_with_crossfade():
    loop = tone(2.0, 0.3)
    out = da.loop_to(loop, 5 * SR)
    assert out.shape == (5 * SR, 2)
    assert np.allclose(out[:SR], loop[:SR])
    short = da.loop_to(np.ones((10, 2), np.float32), 35)   # 比淡化還短：直接接
    assert short.shape == (35, 2) and np.all(short == 1)


def test_mix_at_places_by_start_and_clips_overflow():
    one = np.ones((SR, 2), np.float32)
    out = da.mix_at(2 * SR, [(0.5, one), (1.0, one), (3.0, one)])
    assert out[int(0.25 * SR), 0] == 0 and out[int(0.75 * SR), 0] == 1 and out[int(1.2 * SR), 0] == 2
    assert out[int(1.8 * SR), 0] == 1   # 第二段延伸到 2.0 秒、超出 n 的截掉
    assert out.shape == (2 * SR, 2)


def test_pcm_and_write_wav_round_trip(tmp_path):
    x = tone(0.5, 0.25)
    p = da.write_wav(tmp_path / "t.wav", x)
    y = da.pcm(p)
    assert y.shape == x.shape and np.allclose(y, x, atol=1e-3)
    assert len(da.pcm(p, 0.1, 0.2)) == pytest.approx(0.2 * SR, abs=2)
