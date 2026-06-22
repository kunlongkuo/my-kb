# 別再無腦使用 Playwright 「猜」網頁了，用 Webwright 接上 LLM 「讀」網頁

我們都習慣安裝 Playwright MCP/Skill 來讀取網頁內容並丟入 Context Window 中。事實上，Playwright 原本是為網頁自動化測試而生的產品，你用它讀出來的原始碼還是要給 LLM 「猜」，中間混雜了大量不重要的雜訊，導致有時結果會一直出錯。

微軟最近開源了全新的 Webwright 框架。這是一個擁有「終端機控制權」的瀏覽器自動化 Skill。當你要求 Coding Agent 去讀一個網頁時，Webwright 雖然底層依然會啟動 Playwright，但它不會無腦將內容全塞進 Context Window。相反地，它會讓 Agent 在終端機裡先檢視抓回來的資料，自主決定下一步動作。

過去的做法通常是看完網頁後單次預測下一步，但 Webwright 的強大之處在於，它會直接在本地端產生並迭代一個可重複執行的 Python 腳本（而不僅僅是規劃步驟）。它能像工程師一樣自己寫扣、執行，必要時還會透過無頭瀏覽器截圖 (Screenshot) 來進行自我驗證，確認抓下來的東西完全正確才宣告完成。這不僅讓擷取複雜資料的正確率大幅提高，產出的腳本以後還能重複使用！

## 如何安裝？
直接進入 Claude Code，然後輸入：
> 「根據 https://github.com/microsoft/Webwright 這個網頁，幫我安裝 Webwright skill」

稍等一下就安裝完成了。

安裝完並重啟 Claude Code 後，要使用時只需輸入：
> 「/webwright run 幫我查 NBA 東區冠軍賽的結果」

它就會開始自主制定計畫並執行。當然，簡單的工作不需要動用到它，但較複雜的長流程網頁任務交給 Webwright 準沒錯。
