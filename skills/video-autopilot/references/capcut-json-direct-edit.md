> 來自 video-autopilot-kit 開源知識庫 · MIT 授權
> 原始檔：https://github.com/Hao0321/video-autopilot-kit/blob/main/knowledge/capcut-json-direct-edit.md

JSON Direct Edit（Path D）— **0 GUI / 0 agent token / <1 分鐘完成**

> 比 spawn agent 操作 CapCut GUI 便宜 100x。
> 適用：text content / font / size / position / volume 變更。
> 不適用：套新模板（template_id 要下載）、加貼圖、新 transition。

---

## CapCut Draft JSON 結構速查

### File location
```
C:\Users\<USERNAME>\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\<PROJECT>\
├── draft_content.json   ← CapCut 讀這個 render
├── draft_info.json      ← copy of draft_content（M18 規則：同步改 2 個）
├── Resources/
├── Timelines/<UUID>/draft_content.json  ← 也要同步改（M18 規則）
└── ...
```

---

## ⚠️ M18 升級 — JSON edit 必同步 3 處

CapCut 開專案時優先讀 `Timelines/<UUID>/draft_content.json`，會覆蓋 root 版本。

**強制同步腳本**：
```python
import shutil
from pathlib import Path
DRAFT = Path(r"C:\Users\<USERNAME>\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\<PROJECT>")
root = DRAFT / 'draft_content.json'
for tl in (DRAFT / 'Timelines').iterdir():
    if tl.is_dir():
        tl_dc = tl / 'draft_content.json'
        if tl_dc.exists():
            shutil.copy(root, tl_dc)  # sync from root
```

---

## 改 caption 文字（保留花字效果）

```python
import json
from pathlib import Path

DRAFT = Path(r"C:\Users\<USERNAME>\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\<PROJECT>")

mapping = {
    'old_text_1': 'new_text_1',
    'old_text_2': 'new_text_2',
}

for fname in ['draft_content.json', 'draft_info.json']:
    p = DRAFT / fname
    d = json.load(open(p, encoding='utf-8'))
    for t in d.get('materials', {}).get('texts', []):
        content_str = t.get('content', '{}')
        co = json.loads(content_str)
        old = co.get('text', '')
        new = mapping.get(old)
        if new is None: continue
        co['text'] = new
        # IMPORTANT: 更新 styles[].range 對應新 text 長度
        for s in co.get('styles', []):
            if 'range' in s:
                s['range'] = [0, len(new)]
        t['content'] = json.dumps(co, ensure_ascii=False, separators=(',', ':'))
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=None)
```

---

## 換字體（全部 caption 套同字體）

```python
NEW_FONT = "<專案>/assets/fonts/NotoSerifCJK-Bold.ttc"
for t in d.get("materials", {}).get("texts", []):
    t["font_path"] = NEW_FONT
    co = json.loads(t["content"])
    for s in co.get("styles", []):
        s["font"] = {"path": NEW_FONT, "id": "", "cn_name": "", "tw_name": ""}
    t["content"] = json.dumps(co, ensure_ascii=False, separators=(",", ":"))
```

⚠️ 同步 3 處 JSON（root + draft_info + Timelines）

---

## 改 caption y 位置（上下移動）

```python
# Shorts 標準位置：y = 1280-1400（中央偏下）
# 長片標準位置：y = 820-930

for t in d.get('materials', {}).get('texts', []):
    if 'transform' in t:
        t['transform']['y'] = 1350  # 改成你要的值
```

---

## ⚠️ M41 — 花字效果 JSON 結構（重要坑）

**錯誤假設**：花字效果 = `materials.effects` + `content.styles[].effectStyle.id`

**真相**：CapCut 渲染花字依賴 **`materials.flowers`** 陣列。
- 改 `effectStyle.id` **沒用** — CapCut 不認
- 必須在 `materials.flowers` 加 entry + 在 `segment.extra_material_refs` 指向 flowers entry ID

**結論**：花字效果 **only 可 GUI 套，無法 JSON patch**（除非先 reverse engineer 花字 JSON 結構）。

---

## 常用 JSON 路徑速查

| 要改什麼 | JSON 路徑 |
|---|---|
| Caption 文字內容 | `materials.texts[].content` → 解 JSON → `text` |
| Caption 字體 | `materials.texts[].font_path` + `content.styles[].font.path` |
| Caption Y 位置 | `materials.texts[].transform.y` |
| Caption font_size | `materials.texts[].font_size` |
| 花字效果 | ❌ 無法 JSON patch（走 GUI Path B/C）|
| BGM 音量 | `materials.audios[].volume` |

---

## 快速操作腳本模板

```python
import json, shutil
from pathlib import Path

DRAFT = Path(r"C:\Users\<USERNAME>\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\<PROJECT>")

def load_draft():
    p = DRAFT / 'draft_content.json'
    return json.load(open(p, encoding='utf-8')), p

def save_draft(d, p):
    # 1. 存 root
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    # 2. 同步 draft_info.json
    shutil.copy(p, DRAFT / 'draft_info.json')
    # 3. 同步 Timelines/
    for tl in (DRAFT / 'Timelines').iterdir():
        if tl.is_dir():
            tl_dc = tl / 'draft_content.json'
            if tl_dc.exists():
                shutil.copy(p, tl_dc)

d, p = load_draft()
# ... 做你的修改 ...
save_draft(d, p)
print("✅ 已同步 3 處 JSON，可開 CapCut 確認")
```
