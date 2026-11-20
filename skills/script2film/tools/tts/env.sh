# Qwen3-TTS 環境變數：source 這個檔再跑 clone_lines.py、design_voices.py、speak_lines.py。
# 模型都放在 $S2F_QWEN_TTS_MODELS（底下有 Qwen3-TTS-12Hz-1.7B-Base 等資料夾與 hub/ 快取）。
# 設定檔（~/.config/script2film/config.json）裡環境沒設的鍵先帶進來
eval "$(python3 "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)/tools/config/s2f_config.py" --export)"
# 沒設模型資料夾時用 <S2F_QWEN_TTS_DIR>/../_models（tools/config/s2f_config.py 寫的預設值）
if [ -z "$S2F_QWEN_TTS_MODELS" ] && [ -n "$S2F_QWEN_TTS_DIR" ] && [ -d "$S2F_QWEN_TTS_DIR/../_models" ]; then
  export S2F_QWEN_TTS_MODELS="$(cd "$S2F_QWEN_TTS_DIR/../_models" && pwd)"
fi
if [ -z "$S2F_QWEN_TTS_MODELS" ]; then
  echo "✗ set S2F_QWEN_TTS_MODELS (the folder that holds the Qwen3-TTS models and hub/)" >&2
  return 1 2>/dev/null || exit 1
fi
export HF_HUB_CACHE="$S2F_QWEN_TTS_MODELS/hub"
export TOKENIZERS_PARALLELISM=false
