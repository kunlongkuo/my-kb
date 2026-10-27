---
name: shanshiba-workflow-colab
description: Use ONLY when the user requests the shanshiba-workflow-colab repo, Google Colab G4/MiniMax H3 short-film production, or the 山獅霸 AI 短片雲端流程; guides the repo-specific setup, generation gates, editing, and review.
---

# 山獅霸 Colab AI 短片工作流

使用上游 repo `https://github.com/mathruffian-dot/shanshiba-workflow-colab`，把劇本、首幀、角色聲音、MiniMax H3 影片、配樂、剪接與自審串成一條 Google Colab 工作流。這是 **H3 短片生成流程**，不是一般素材剪輯器。

## 觸發範圍

只有在使用者提到此 repo、Colab G4 跑 H3、或要求用「山獅霸 Colab 流程」製作 AI 短片時啟用。一般影片剪接應改用 `video-production-workflow`、`video-autopilot` 或 `video-use-editor`。

## 開始前必讀上游文件

先取得最新 repo（若工作目錄已有明確指定的 clone，先確認 remote 與分支），並按任務讀取：

1. `README.md`：影片預設規格、主流程、版本差異與授權摘要。
2. `AGENT_SETUP.md`：硬體偵測、Windows 設定與 Agent 操作界線。
3. `cloud/README.md`：Colab CLI、G4 啟動、全雲端／H3-only、運算單元及停機方式。
4. `docs/02_端到端流程.md`、`docs/03_規則與踩坑.md`、`docs/04_自審清單.md`：製作關卡、H3 鏡頭規則與成片 QA。
5. `pipeline/template_local/README.md` 與 `pipeline/template_local/film.json`：專案設定欄位與 stage 執行方法。
6. `THIRD_PARTY_NOTICES.md`：逐項確認目前模型與素材授權；不要只依賴本技能摘要。

上游來源：

- [Repo 首頁與 README](https://github.com/mathruffian-dot/shanshiba-workflow-colab)
- [Colab 工作流](https://github.com/mathruffian-dot/shanshiba-workflow-colab/blob/main/cloud/README.md)
- [Agent 安裝手冊](https://github.com/mathruffian-dot/shanshiba-workflow-colab/blob/main/AGENT_SETUP.md)
- [端到端流程](https://github.com/mathruffian-dot/shanshiba-workflow-colab/blob/main/docs/02_端到端流程.md)
- [規則與踩坑](https://github.com/mathruffian-dot/shanshiba-workflow-colab/blob/main/docs/03_規則與踩坑.md)
- [自審清單](https://github.com/mathruffian-dot/shanshiba-workflow-colab/blob/main/docs/04_自審清單.md)

## 不可略過的啟動閘門

### Colab 帳號、額度與 Windows

- 開跑前執行 `python setup/detect_hardware.py`，採用 repo 對目前硬體提出的路徑。
- Windows 依上游指示安裝 `google-colab-cli` 並執行 `python cloud/colab_cli_windows_patch.py`；Patch 會修改已安裝的 CLI，先說明其作用。
- Google 登入只能由使用者在自己的終端機執行 `colab usage`；Agent 不可代收、讀取或要求貼上授權碼／Token。
- 授權後以 `python cloud/colab_h3.py check` 核對餘額。若餘額不足、為零或無法確認，停止在雲端啟動前。
- 預設只用使用者已持有的額度；**購買運算單元、升級訂閱或產生其他付費前，必須先取得明確同意**。執行前報告階段、時間及可查得的用量估算，不把估值說成保證。

### MiniMax H3 與 Colab 機房地區

上游文件指出，MiniMax H3 授權排除美國、歐盟、英國與南韓；Colab G4 實測機房常在美國／歐盟。將此限制和上游最新說明告知使用者，**明確確認其選擇後才可在 G4 啟動 H3**。若不接受或未答覆，不執行 H3；可停在劇本／分鏡或改查合適的替代執行環境。

### 模型與內容授權

- 讀 `THIRD_PARTY_NOTICES.md`。特別確認商業用途：Qwen-Image 2.1、Breeze TTS 2 等元件有非商業限制；不得預設此工作流可營利。
- MiniMax H3／Music 3 公開發布需遵守其 AI 生成揭露與模型名稱標示要求；成片片尾和發布文字依實際使用項目列示。
- 不模仿未經同意的真人臉或聲音；不可把 API key、私人素材或授權憑證寫入專案、Log 或 Git。

## 標準製作流程與人工關卡

依上游最新模板製作；repo 標準為橫式 **16:9、24fps**、短片常見 1–3 分鐘，單一 H3 鏡頭不超過 12 秒。使用者另有規格時，先記錄差異並確認相容性。

1. **前期**：使用 `shanshiba-drama` 產出故事、劇本、鏡表及生成前試映；先讓使用者審閱通過。故事稿和試映未通過前，不批次生圖或影片。
2. **角色／場景／首幀**：依 `film.json` 建立原創角色和場景，執行 `chars masters frames`。下載 `out/first/_sheet.jpg` 後停下，讓使用者確認角色一致性、構圖與背景。
3. **角色聲音／H3**：依最新模板建立角色參考音，再逐鏡生成 H3。每鏡只保留需要入鏡的角色、單一說話者；`action` 依 repo 現行規則寫 50–120 個英文單字。檢查 `out/review/clips_*.jpg`、逐鏡聽寫與台詞後停下供使用者審看；不合格鏡頭修正後再進下一步。
4. **剪輯／音樂／輸出**：再執行 `amb edl music ending cut review`（按實際 stage 和 repo 最新版調整）。Linux／Colab 不使用僅限 Windows 的 RTX VSR；按 repo 設定採用有效的放大方式。
5. **最終 QA**：完成自審五遍，檢查換臉、多手多腳、背景漂移、台詞、黑畫面、凍格、剪點、響度、字幕與授權標示；交付前仍要讓使用者完整看成片。

`cloud/colab_h3.py film` 要求 `film_dir` 位於 repo 目錄下（`cmd_film` 會將它解析為相對 repo 路徑）。若成品專案保存在知識庫其他位置，先在暫存 clone 的 `pipeline/<片名>/` 建立工作副本，設定 `repo_dir` 並保留可回同步的輸出；不可把暫存 clone 當成使用者最終成品目錄。

## Colab 操作提示

依上游版本使用正確命令，不要臆測參數：

```powershell
python cloud/colab_h3.py check
python cloud/colab_h3.py start
python cloud/colab_h3.py film pipeline/<片名> chars masters frames
python cloud/colab_h3.py film pipeline/<片名> voices h3
python cloud/colab_h3.py film pipeline/<片名> amb edl music ending cut review
python cloud/colab_h3.py stop
```

`start` 預設完整安裝；只有本機前置階段已完成、且確定只需 H3 時才考慮 `--h3-only`。審片與重拍期間依 `cloud/README.md` 保留或管理 Colab session；全部完成後才停止 VM。遇到錯誤、額度不明或機房風險時停止，不繞過機械閘門。

## 授權與出處

上游程式碼採 MIT；上游文件與素材採 CC BY-NC 4.0；第三方模型各有獨立條款。此技能是供 Agent 呼叫上游流程的操作入口，不複製上游 repo 全文或模型權重。引用上游文件時保留來源：`mathruffian-dot / shanshiba-workflow-colab`，並遵守其授權與第三方聲明。
