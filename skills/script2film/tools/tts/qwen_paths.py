"""Where the Qwen3-TTS models are: $S2F_QWEN_TTS_MODELS (the old name QWEN_TTS_MODELS also works), else
<$S2F_QWEN_TTS_DIR>/../_models, the same rule doc_tts.py follows. The models are not shipped with the repo."""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import os
import sys
from pathlib import Path


def models_dir(environ):
    """Folder of the Qwen3-TTS models: S2F_QWEN_TTS_MODELS (old name QWEN_TTS_MODELS) when set, otherwise
    <S2F_QWEN_TTS_DIR or QWEN_TTS_DIR>/../_models (the same default as doc_common.qwen_models_dir and env.sh).
    None when neither is set."""
    root = environ.get("S2F_QWEN_TTS_MODELS") or environ.get("QWEN_TTS_MODELS")
    if root:
        return Path(root).expanduser()
    tts = environ.get("S2F_QWEN_TTS_DIR") or environ.get("QWEN_TTS_DIR")
    return Path(tts).expanduser().parent / "_models" if tts else None


VOICE_LANG = {"zh": ("Chinese", True), "en": ("English", False)}   # a cast entry's "lang" -> (the model's language, convert to Simplified first)


def voice_language(lang):
    """(language for Qwen3-TTS, convert the text to Simplified Chinese first) for a cast entry's "lang" (the same values
    as doc.json "lang"); an entry without one is "zh"."""
    lang = lang or "zh"
    if lang not in VOICE_LANG:
        sys.exit(f'✗ "lang": {lang!r} is not supported here: use "zh" or "en"')
    return VOICE_LANG[lang]


def model(name):
    root = models_dir(os.environ)
    if root is None:
        sys.exit("✗ set S2F_QWEN_TTS_DIR (the qwen3-tts folder) or S2F_QWEN_TTS_MODELS (the folder that holds the models)")
    path = root / name
    if not path.is_dir():
        sys.exit(f"✗ model not found: {path}")
    return path
