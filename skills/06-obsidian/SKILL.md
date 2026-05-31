---
name: antigravity-obsidian
description: 在 AntiGravity 連接 Obsidian MCP (MCPVault)。說「連接 Obsidian」「設定 Obsidian」時載入。
---

# 連接 Obsidian（AntiGravity 版）

## 步驟

### 1. 找到 vault
請先確認 Obsidian vault 的實體路徑。
- `I:\Mark\my-kb\raw\obsidian`

### 2. 安裝 MCPVault
在命令提示字元或 PowerShell 中執行安裝：
```powershell
npm.cmd install -g @bitbonsai/mcpvault
where.exe mcpvault
```
常見安裝路徑：
```
C:\Users\Mark\AppData\Roaming\npm\mcpvault.cmd
```

### 3. 註冊 Obsidian MCP
在 AntiGravity 的 MCP 設定檔（如 `opencode.json`）加入以下內容：
```json
{
  "obsidian": {
    "type": "local",
    "command": [
      "C:\\Users\\Mark\\AppData\\Roaming\\npm\\mcpvault.cmd",
      "I:\\Mark\\my-kb\\raw\\obsidian"
    ],
    "enabled": true
  }
}
```
若使用 `command / args` 分離格式，可寫成：
```json
{
  "command": "C:\\Users\\Mark\\AppData\\Roaming\\npm\\mcpvault.cmd",
  "args": ["C:\\Users\\Mark\\Documents\\Obsidian Vault"]
}
```

### 4. 測試與驗證
1. 重啟 AntiGravity 以載入新 MCP 設定。\n2. 執行 `mcp list` 或相關指令，確認 Obsidian vault 已被偵測。\n3. 手動建立測試筆記，驗證 AI 能讀寫 Obsidian 中的筆記。

---
> **安全提醒**\n> - 不要將 MCP 設定檔直接 commit 到公開 repo。\n> - 確認 vault 路徑不含個人敏感資訊。\n> - 若有多個 vault，請在設定檔中分別新增相應條目。
