# Configuration

## 設定原則

- 設定與知識內容分離；實際憑證只放在使用者自行管理的私有設定檔，不要放入 Skill、索引或版本控制。
- `templates/setup.example.json` 僅是欄位範例。複製後由使用者自行填寫，不要將範例值當成真實帳密。
- 不要在回答、日誌或命令輸出中顯示 API key、密碼或完整設定檔。

## 欄位

- `mysql.host`、`mysql.port`、`mysql.user`、`mysql.password`、`mysql.database`：MySQL 連線設定。
- `openai.api_key`：API key；隨附腳本目前要求此欄位存在，但不會呼叫 OpenAI API。
- `openai.chat_model`、`openai.embedding_model`：模型名稱欄位；目前只作為索引 metadata，不會執行模型推論或 embedding。
- `rag.chunk_size`、`rag.chunk_overlap`：切段大小與重疊；隨附腳本會使用。
- `rag.top_k`：設定範例欄位；查詢時腳本以 `--top-k` 參數為準。
- `rag.score_threshold`、`rag.rebuild_mode`：設計欄位；隨附腳本目前未使用。

## 驗證設定

如使用者已準備私有設定檔，可執行：

```bash
python <skill-dir>/scripts/skill_rag.py --setup <private-setup.json> validate-config
```

驗證只檢查必要欄位格式，並不測試 MySQL 連線或 OpenAI 金鑰有效性。避免把設定檔內容或命令輸出中的識別資訊貼入對話。
