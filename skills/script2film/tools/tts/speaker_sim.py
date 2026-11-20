"""語者相似度（ECAPA，speechbrain spkrec-ecapa-voxceleb）：拿一段「真的本人」當基準，量每個候選像不像。

用法：<有 speechbrain 的 Python> tools/tts/speaker_sim.py <基準.wav> <候選.wav|資料夾>...
同一人不同句約 0.8–0.9，不同人多在 0.4 以下（我們的實測）。
模型快取的位置由 S2F_SPEECHBRAIN_CACHE 決定（沒設用 ~/.cache/script2film/speechbrain-ecapa）。
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import os
import sys
from pathlib import Path

import soundfile as sf
import torch
import torchaudio
from speechbrain.inference.speaker import EncoderClassifier

CACHE = Path(os.environ.get("S2F_SPEECHBRAIN_CACHE") or Path.home() / ".cache/script2film/speechbrain-ecapa")


def embed(model, path: Path) -> torch.Tensor:
    data, sr = sf.read(str(path), dtype="float32", always_2d=True)  # torchaudio.load 要 torchcodec，改用 soundfile
    wav = torch.from_numpy(data.T).mean(0, keepdim=True)
    if sr != 16000:
        wav = torchaudio.functional.resample(wav, sr, 16000)
    return model.encode_batch(wav).squeeze()


def main(ref: str, targets: list[str]):
    model = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir=str(CACHE),
                                           run_opts={"device": "cpu"})
    base = embed(model, Path(ref))
    files = []
    for t in targets:
        p = Path(t)
        files += sorted(p.glob("*.wav")) if p.is_dir() else [p]
    for f in files:
        sim = torch.nn.functional.cosine_similarity(base, embed(model, f), dim=0).item()
        print(f"{sim:.3f}  {f}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Speaker similarity (ECAPA, speechbrain spkrec-ecapa-voxceleb): how much each candidate sounds like a clip of the real person.\n\n"
                 "Usage: <a Python with speechbrain> tools/tts/speaker_sim.py <reference.wav> <candidate.wav|folder>...\n"
                 "The same person on different lines scores about 0.8–0.9; different people mostly below 0.4 (our measurements).\n"
                 "The model cache is S2F_SPEECHBRAIN_CACHE (default ~/.cache/script2film/speechbrain-ecapa).")
    main(sys.argv[1], sys.argv[2:])
