# design.md 筆記

> 來源：[是 Ray 不是 Array — design.md？如果你使用 AI 畫面總是跑掉，那肯定是因為你沒導入 Google 的 design.md](https://israynotarray.com/ai/20260627/1947382651/)
> 日期：2026-06-27

---

## 🧐 什麼是 design.md？

`design.md` 是 **Google Labs 開源**的一種格式規範（Apache 2.0），最早從 Google AI 設計工具 **Stitch** 孵化而來。

目的是讓 **Claude Code、Cursor、GitHub Copilot** 等 AI Coding 工具能夠**精準讀懂你的設計系統**，從而在生成 UI 時維持一致的顏色、字級、間距、圓角。

- GitHub：[google-labs-code/design.md](https://github.com/google-labs-code/design.md)

---

## 🤔 它解決了什麼問題？

用 AI 生 UI 最常遇到的問題：**每次產出的顏色、字級都不一樣**。

- 第一次給 `#3B82F6`
- 第二次給 `#2563EB`
- 第三次給 `bg-blue-500`

根本原因：沒有給 AI 一份「設計系統規則」的結構化文件。

### 跟 CLAUDE.md / AGENTS.md 的差別

| 文件 | 類型 | 說明 |
|------|------|------|
| `CLAUDE.md` / `AGENTS.md` | 自然語言規則 | AI 還是要靠「猜」來決定用哪個顏色 |
| `design.md` | 結構化設計系統 | 機器能精準讀取 + 人類能讀懂理由 |

---

## 📄 design.md 的結構

由兩塊組成：

### 1. YAML Front Matter（Token 區塊）

放精確的設計 Token：顏色、字體、間距、圓角、元件。

```yaml
---
name: Heritage
colors:
  primary: "#1A1C1E"
  secondary: "#6C7278"
  tertiary: "#B8422E"
  neutral: "#F7F5F2"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 3rem
  body-md:
    fontFamily: Public Sans
    fontSize: 1rem
rounded:
  sm: 4px
  md: 8px
spacing:
  sm: 8px
  md: 16px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    rounded: "{rounded.sm}"
---
```

**重點：**
- 五大 Token 類別：`colors`、`typography`、`rounded`、`spacing`、`components`
- Token 之間可以**互相引用**，例如 `"{colors.tertiary}"`，改一處全部跟著變
- 顏色支援所有合法 CSS 格式：hex、rgb、hsl、oklch

### 2. Markdown 內文（設計理由）

放給人（和 AI）讀的設計原因，官方推薦章節順序：

1. **Overview**（概觀）
2. **Colors**（顏色）
3. **Typography**（字級）
4. **Layout**
5. **Elevation & Depth**
6. **Shapes**
7. **Components**
8. **Do's and Don'ts**

> 只有 `Colors` 中的 `primary` 顏色是**必填**的，其他都是選填。

**範例寫法：**

```markdown
## Colors

Primary (#1A1C1E): Deep ink for headlines and core text.
Use on light surfaces to maximize legibility.

Tertiary (#B8422E): Warm rust accent reserved for primary actions
and brand moments. Avoid using as body text colour due to contrast.
```

---

## 🛠️ 內建 CLI 工具

### 安裝

```bash
npm install @google/design.md
npx @google/design.md lint DESIGN.md
```

> **Windows 注意**：`.md` 副檔名可能被系統吃掉，改用 alias：
> ```bash
> npx -p @google/design.md designmd lint DESIGN.md
> ```

### 四大功能

#### `lint`：驗證結構

檢查：
- YAML schema 是否正確
- Token 引用是否有壞掉（例如拼錯字）
- 是否有 `primary` 顏色
- **WCAG AA 對比度**是否通過（無障礙檢查整合進來了！）
- 是否有定義了卻沒人用的 orphan token
- 章節順序是否符合推薦

#### `diff`：比較兩個版本差異

```bash
npx @google/design.md diff old/DESIGN.md new/DESIGN.md
```

列出哪些 Token 改了、刪了、新增了，方便評估設計版本升級的影響範圍。

#### `export`：轉成其他格式

| 格式 | 說明 |
|------|------|
| `json-tailwind` | 轉成 Tailwind v3 的 config 物件 |
| `css-tailwind` | 轉成 Tailwind v4 的 `@theme` CSS 區塊 |
| `dtcg` | 轉成 W3C Design Tokens Format Module |

```bash
npx @google/design.md export DESIGN.md --format json-tailwind > tailwind.config.js
npx @google/design.md export DESIGN.md --format css-tailwind > tailwind.css
npx @google/design.md export DESIGN.md --format dtcg > design-tokens.json
```

**優勢**：只維護一份 `design.md`，前端、設計師、AI Coding 工具用同一份 source of truth。

#### `spec`：輸出格式規範給 AI

```bash
npx @google/design.md spec
```

輸出 design.md 自己的格式規範，可以塞給 AI Coding 工具，讓它知道如何正確解讀 DESIGN.md。

加上 `--rules` 可一併輸出 linting 規則。

---

## 📥 怎麼取得 DESIGN.md？

1. **手動建立**：照著 YAML + Markdown 結構自己寫
2. **從現成範本挑**：[VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) 有各種風格的範本，直接丟到專案根目錄即可

---

## 🤖 怎麼搭配 AI Coding 工具使用？

1. 把 `DESIGN.md` 放在**專案根目錄**
2. 在 `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/*.mdc` 裡面加一句：
   > 「請在做 UI 相關任務時優先讀 `DESIGN.md`，並嚴格遵守裡面的 Token 與設計理由。」

### ⚠️ 注意事項

- **不要塞太多無關的東西**：design.md 的設計理念是給 AI「精煉過的設計知識」，給重點不是給全部
- 目前沒有 Claude Code / Cursor / Copilot 的**官方整合範例**，只有 CLI 和 TypeScript API，需要靠 CLAUDE.md / AGENTS.md 手動引導 AI 去讀

---

## 💡 Google 開源的商業邏輯（有趣的觀察）

- **拿到標準定義權**：類似 OpenAPI、Kubernetes，開源後 Google 主導規範走向
- **讓競爭工具幫忙推廣**：Cursor、Copilot 若支援 design.md，等於替 Google 免費行銷
- **訓練資料 flywheel**：公開 repo 的 design.md 成為 Gemini 訓練 AI 生 UI 的黃金資料
- **Stitch 的免費漏斗**：開發者習慣 design.md 後，最自然想找 Stitch（源頭）當設計工具

---

## 📝 總結

| 項目 | 內容 |
|------|------|
| **是什麼** | YAML Token + Markdown 設計理由的混合格式文件 |
| **解決什麼** | AI 產 UI 時顏色、字級、間距前後不一致 |
| **CLI 功能** | lint（含 WCAG）、diff、export（Tailwind/DTCG）、spec |
| **怎麼用** | 放根目錄 + 在 AGENTS.md 引導 AI 讀它 |
| **取得方式** | 手動寫 或 awesome-design-md 挑範本 |
