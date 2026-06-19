---
name: antigravity-workflow
description: AntiGravity 開工/收工/新專案初始化流程。說「開工」「收工」「初始化專案」時載入。
---

# 開工 / 收工 / 新專案初始化

## 開工
1. 讀取 `ANTIGRAVITY.md`
2. 讀取專案筆記重點
3. `git status` + 最近 commit
4. 回報狀態與建議下一步
5. 不自動 pull/commit/push

## 收工
1. 檢查敏感資料（API key、token、學生真名等）
2. 更新 `README.md`，寫清楚：專案用途、目前功能、啟動方式、部署方式、環境變數、已知問題、下一步
3. 更新 `docs/PROGRESS.md`，以日期記錄：今天完成什麼、改了哪些重要檔案、做了哪些決策、目前卡在哪裡、下次接手要先看什麼
4. 更新專案筆記（完成事項、下一步、踩坑）
5. 只在規則改變時更新 ANTIGRAVITY.md
6. 檢查 git status + diff
7. 只 stage 本次相關檔案（不用 `git add .`）
8. 確認後 commit + push（commit message 必須寫清楚改動內容與細節，拒絕無語意的 "update"）
9. 回報同步結果

## 新專案初始化
先問：名稱、用途、資料夾、是否 GitHub repo、公開/私有、是否部署。
建立：ANTIGRAVITY.md、README.md、.gitignore、Git repo、GitHub repo、專案筆記。
若已存在 → 盤點後只補缺口，不覆蓋。
