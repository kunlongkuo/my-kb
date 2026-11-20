# 範例：小咖啡店的兩種做法

一支五句話、約 23 秒的解說片，示範兩件 `examples/coffee` 沒有的事：一個外部生成的鏡頭（第 1 拍），和一位對嘴的主持人（前兩拍在左下圓框、最後一拍全版）。內容是虛構的。

主持人是 AI 生成的虛構人物，聲音是用文字描述設計出來的合成聲音；不是任何真人的長相、錄音或克隆。

先做過 `examples/coffee`（英文旁白的範例）再來做這個。

## 兩條路

### 用預製素材（不用任何帳號或金鑰）

`premade/` 裡附了做好的旁白、鏡頭與主持人。把它們放進專案，跳過配音與生成，從對時（F3）往下做：

```
python3 skills/ve-director/doc/scripts/doc_lint.py examples/brewing/doc.json
cp -R examples/brewing/premade/. examples/brewing/
python3 skills/ve-director/doc/scripts/doc_align.py examples/brewing/doc.json
python3 skills/ve-director/doc/scripts/doc_lint.py examples/brewing/doc.json --beats examples/brewing/beats.json
python3 skills/ve-director/doc/scripts/doc_code.py examples/brewing/doc.json --render
python3 skills/ve-director/doc/scripts/doc_host.py join examples/brewing/doc.json
python3 tools/ve-runner/ve_clipcheck.py examples/brewing/ve_flat --strips
python3 skills/ve-director/doc/scripts/doc_cut.py examples/brewing/doc.json --render
python3 tools/nightly/check.py examples/brewing/doc.json examples/brewing/cut_lecture-finance/output.mp4
```

- 每一步做對了的樣子寫在 `docs/FLOW.md` 的 F1、F3 到 F6。
- 不用帳號，但對時那一步仍要你電腦上的語音轉錄（`docs/FLOW.md` F0 的安裝檢查會查）。
- **不要跑 F2（配音）。** 附上的主持人是照 `premade/tts/voice.wav` 這一條旁白對嘴的；重新配音之後，嘴型和長度都對不上，主持人就要自己重做。

### 自己生成（要有生成鏡頭與對嘴主持人的工具）

照 `docs/FLOW.md` 從 F0 做到 F6，加上選用 A（鏡頭）與選用 B（主持人）。用 VideoExpress、TalkingPhotos 以外的平台也可以：把做好的檔照選用 A、B 各自「Using another platform」那一節的資料夾約定放好，後面的步驟不用改。

- 第 1 拍要畫什麼，寫在 `doc.json` 的 `shots.two_brews`。
- 主持人的造型圖是 `refs/host_look.jpg`。要換成別人，照選用 B「The look image」的規則先做候選圖、挑定了再上傳；換了人，聲音也要換成配得上的（`refs/voice_cast.json` 是設計聲音用的描述）。
- 換了造型圖，`doc.json` 的 `pip.crop` 要跟著調到圓框對到臉。

## 做完會看到什麼

- `cut_lecture-finance/output.mp4`：成片。第 1 拍是吧台上的手沖壺與義式機，左下圓框裡有主持人；第 2 拍是清單加圓框；第 3、4 拍是左右對照與算式；第 5 拍主持人全版。
- 長度落在 `expected.json` 的 `seconds` 範圍內。走預製素材那條路是 23.5 秒。
- F6 的檢查退出碼是 0。它會列出兩拍 sparse cards（畫面偏空的卡），那是只列不擋的提醒。
- F1 的檢查會印一條 `⚠ ai_phrasing`（第 1 句的「做法」），也是提醒，最後一行仍是 `doc_lint: ok`。
- 自己配音時，第 4 句的吻合度可能低於 0.85：轉錄把「一百八」寫成 180、「義式」寫成同音字。看 `tts/lines.json` 那一句的 `heard`，字都有唸到就不用重配。

做片的產出都列在倉庫根目錄的 `.gitignore` 裡，不會進版控。要清掉：

```
git clean -ndX examples/brewing    # 先看會刪什麼
git clean -fdX examples/brewing    # 只刪被忽略的檔（做片的產出；premade/ 不會被刪）
```

## 檔案

| 檔 | 內容 |
|---|---|
| `doc.json` | 五句旁白、五拍、色版 `lecture-finance`；`pip` 是圓框的設定，`shots` 是第 1 拍的鏡頭描述 |
| `refs/host_look.jpg` | 主持人造型圖：AI 生成的虛構人物（純文字生成，沒有用任何人的照片當參考） |
| `refs/narrator.wav`、`refs/narrator.txt` | 參考聲音與它唸的那句話：合成聲音，不是任何真人 |
| `refs/voice_cast.json` | 設計這個聲音用的描述與 seed |
| `premade/tts/voice.wav`、`premade/tts/lines.json` | 配好的旁白與每句的起訖 |
| `premade/ve_flat/shot1.mp4` | 第 1 拍的鏡頭（用 VideoExpress 生成） |
| `premade/host/parts/part1.mp4`、`premade/host/parts.json` | 主持人一段（用 TalkingPhotos 生成，無聲）與它在旁白裡的位置 |
| `expected.json` | 做對了的樣子：拍數、句數、成片秒數的範圍；`script_approved` 是審過的旁白的指紋（旁白原樣不動，F2 不必帶 `--script-approved`；改了任何一句就要使用者重新核可） |

`premade/` 與 `refs/` 各檔的來源與授權在倉庫根目錄的 `NOTICE.md`。
