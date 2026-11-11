// 在 Gemini／Flow 頁面以 javascript_tool 執行的輔助片段（Claude in Chrome）。
// 每段獨立貼上執行；不要整檔一次執行。

// ---- A. 攔截隱藏的 <input type=file>，讓 file_upload 工具找得到（點「上傳檔案」前先執行）----
window.__origClick = window.__origClick || HTMLInputElement.prototype.click;
HTMLInputElement.prototype.click = function () {
  if (this.type === 'file') {
    if (!this.isConnected) document.body.appendChild(this);
    this.style.cssText = 'display:block;position:fixed;top:5px;left:5px;width:120px;height:30px;z-index:99999';
    this.setAttribute('aria-label', 'claude upload input');
    window.__fileInput = this;
    return;
  }
  return window.__origClick.call(this);
};
// 之後：用「真的點擊」(computer left_click ref) 點上傳鈕 → find "claude upload input" → file_upload。
// 上傳完還原：
HTMLInputElement.prototype.click = window.__origClick;
if (window.__fileInput) window.__fileInput.style.cssText = 'display:none';

// ---- B. Gemini：開「建立影片」工具（上傳前執行；mi=false 時改用 find 點選）----
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  document.querySelector('button[aria-label="上傳與工具"]')?.click();
  let mi = null;
  for (let i = 0; i < 20 && !mi; i++) {
    await sleep(200);
    mi = [...document.querySelectorAll('[role=menuitemcheckbox]')].find(e => e.textContent.includes('建立影片'));
  }
  mi && mi.click();
  return !!mi;
})();

// ---- C. Flow：在「首幀模式」選某張已上傳圖當首幀、輸入框取得焦點（之後用 computer type 打提示詞）----
(async (NAME) => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  [...document.querySelectorAll('button')].find(b => b.innerText.trim() === '開始').click();
  await sleep(1500);
  [...document.querySelectorAll('[role=option]')].find(o => o.innerText.includes(NAME))?.click();
  await sleep(800);
  [...document.querySelectorAll('button')].find(b => b.innerText.trim() === '新增至提示詞')?.click();
  await sleep(1500);
  document.querySelector('div[contenteditable=true]').focus();
  return document.body.innerText.includes('cancel\nswap_horiz');   // true = 首幀已設定
})('s05.jpg');

// ---- D. Flow：確認提示詞與首幀都在才送出 ----
(async (KEY) => {
  const tb = document.querySelector('div[contenteditable=true]');
  const ok = tb.innerText.includes(KEY) && document.body.innerText.includes('cancel\nswap_horiz');
  if (ok) document.querySelector('button[type=submit]').click();
  return ok;
})('提示詞中的一個獨特關鍵字');

// ---- E. Flow：替所有影片卡的下載鈕加上可 find 的標籤（下載仍需用 computer left_click 逐一點）----
(() => {
  const v = [...document.querySelectorAll('button')].filter(b => b.innerText.trim() === 'download').filter(b => {
    let c = b; for (let i = 0; i < 6; i++) { c = c.parentElement; if (c.innerText.includes('建立時間')) break; }
    return c.innerText.includes('Veo 3.1');
  });
  v.forEach((b, i) => b.setAttribute('aria-label', 'claude-dl-' + i));
  return v.length;
})();
