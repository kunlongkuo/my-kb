#!/bin/zsh
# tp_submit.sh <audio label, e.g. "Ep01 part2"> <render name> [造型，例如 "Host shirt"]
# 不給造型：全新流程 → Choose Previous Character 照名字選原版（TP_ORIGINAL，原版角色在 TP 的名稱；沒有預設，沒設就停下）。
# TP_ASPECT（預設 16:9，直式給 9:16；新角色與原版角色都照它選）、TP_GENDER（預設 male，女性給 female）。
# 給造型：從頭開新流程（Create Video → Human Video），Create New Character → Use Directly From Library → Images 資料夾選那張圖，
# 原圖直接當角色、不重畫臉（實測）。造型圖要先在 TP 媒體庫 Images 裡（tp_upimg.py 上傳）。
cd "${0:A:h}"
eval "$(python3 ../config/s2f_config.py --export)"   # 設定檔（~/.config/script2film/config.json）裡環境沒設的鍵
e(){ python3 tp_browser.py eval "$1" 2>/dev/null; }
# 「Import Audio」大按鈕要真的滑鼠點才開媒體庫（JS click 沒反應）
xy(){ e "(()=>{const b=[...document.querySelectorAll('button')].filter(b=>b.offsetParent&&b.innerText.trim()==='$1').pop();if(!b)return 'none';const r=b.getBoundingClientRect();return Math.round(r.x+r.width/2)+' '+Math.round(r.y+r.height/2)})()" | tr -d '"'; }
c(){ e "(()=>{const b=[...document.querySelectorAll('button')].filter(e=>e.offsetParent&&e.innerText.trim().startsWith('$1'));if(!b.length)return 'none:$1';b[b.length-1].click();return 'ok:$1'})()"; sleep ${2:-3}; }
t(){ python3 tp_browser.py click "$1" >/dev/null 2>&1; sleep ${2:-3}; }   # 照文字點（真實滑鼠事件）
card(){ e "(()=>{const l=[...document.querySelectorAll('*')].find(e=>e.offsetParent&&e.children.length===0&&e.textContent.trim()==='$1');if(!l)return 'none';l.scrollIntoView({block:'center'});const r=l.getBoundingClientRect();return Math.round(r.x+r.width/2)+' '+Math.round(r.y-100)})()" | tr -d '"'; }
if [[ -n $3 ]]; then
  # 用 hash 進 create-video 會停在上一次的步驟、退不回角色頁；從 Create Video 彈窗進才是全新流程
  e "(()=>{location.hash='#/homepage';return 1})()" >/dev/null; sleep 3
  t "Create Video" 4; t "Human Video" 5
  c "High Quality"; c Next; c "${TP_ASPECT:-16:9}"; c "Create New Character"
  e "(()=>{const s=[...document.querySelectorAll('select')].find(x=>x.offsetParent);s.value=[...s.options].find(o=>/^${TP_GENDER:-male}$/i.test(o.text.trim())).value;s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()" >/dev/null
  t "Use Directly From Library" 4; t "Images" 4
  # Images 也會分頁（圖多了之後，要用的那張掉到第 2 頁就找不到）：先用搜尋框找名字
  pos=none
  for i in {1..3}; do
    python3 tp_browser.py fill "input[placeholder='Search...'] >> visible=true" "$3" >/dev/null 2>&1; sleep $((2 + i))
    pos=$(card "$3"); [[ $pos != none ]] && break
  done
  echo "look $3 $pos"
  [[ $pos == none ]] && { echo "✗ no look \"$3\" in Media Library Images"; exit 1; }
  python3 tp_browser.py clickxy ${=pos} >/dev/null 2>&1; sleep 1; c Select 6
  # 圖的比例和 TP_ASPECT 不合時 TP 會問要不要自動裁切（tp_upimg.py 會先擋；圖本來就在媒體庫時還是會遇到）。
  # 2026-11-16 加入，未實測：那次是使用者手動按掉的。
  [[ $(xy "Yes, do it") != none ]] && c "Yes, do it" 6
  c Next 4
else
  # 原版：清單照時間新到舊排、名字是當時的影片名，第一張是上一集的造型（照順序選第一張會選錯）。
  # 改成全新流程＋照名字找原版那張（TP_ORIGINAL），找不到就翻頁（集數多了會排到後面，實測做到二十幾集時已在第 6 頁，上限 15 頁）。
  orig=$TP_ORIGINAL
  [[ -z $orig ]] && { echo "✗ set TP_ORIGINAL (the original character's name in TP)"; exit 1; }
  e "(()=>{location.hash='#/homepage';return 1})()" >/dev/null; sleep 3
  t "Create Video" 4; t "Human Video" 5
  c "High Quality"; c Next; c "${TP_ASPECT:-16:9}"; c "Choose Previous Character" 4
  for pg in {1..15}; do pos=$(card "$orig"); [[ $pos != none ]] && break; t "Next page" 4; done
  echo "original $orig $pos"
  [[ $pos == none ]] && { echo "✗ original character \"$orig\" not found under Choose Previous Character"; exit 1; }
  python3 tp_browser.py clickxy ${=pos} >/dev/null 2>&1; sleep 1; c Select 5
  # 選先前角色時 Select 就會直接進到 Choose Audio；再按 Next 會跳到 Render、找不到 Import Audio
  [[ $(xy "Import Audio") == none ]] && c Next 4
fi
c "Import Audio" 2; p=$(xy "Import Audio"); python3 tp_browser.py clickxy ${=p} >/dev/null 2>&1; sleep 4
t "${TP_AUDIO_DIR:-Audio}" 4   # 媒體庫資料夾（TP_AUDIO_DIR 換資料夾，預設 Audio）要點文字才打得開（原本點座標 1045 333，換了流程位置會跑掉）
# 音檔多了會分頁（實測到過 10 頁），新傳的不一定在第一頁：用選檔視窗的搜尋框找名字，不翻頁
# 剛上傳的音檔搜尋有時 3 秒內還沒出來（回「card none」，重跑就有）：最多搜 4 次
for i in {1..4}; do
  python3 tp_browser.py fill "input[placeholder='Search...'] >> visible=true" "$1" >/dev/null 2>&1; sleep $((2 + i))
  pos=$(card "$1"); [[ $pos != none ]] && break
done
echo "card $pos"
[[ $pos == none ]] && exit 1
python3 tp_browser.py clickxy ${=pos} >/dev/null 2>&1; sleep 1
e "(()=>{const b=[...document.querySelectorAll('button')].filter(e=>e.innerText.trim().startsWith('Select'));b[b.length-1].click();return 1})()" >/dev/null; sleep 4
e "[...document.querySelectorAll('*')].filter(e=>e.offsetParent&&e.children.length===0&&/\(mp3\)/.test(e.textContent)).map(e=>e.textContent.trim())"
c Next 4
e "(()=>{const i=[...document.querySelectorAll('input')].find(e=>e.offsetParent);i.select();return 1})()" >/dev/null
timeout 30 python3 tp_browser.py fill "input[type=text]" "$2" 2>&1 | tail -1
e "[...document.querySelectorAll('input')].filter(e=>e.offsetParent).map(e=>e.value)"
