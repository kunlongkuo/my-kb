#!/bin/zsh
# tp_swap.sh "<audio label>" "<render name>": from the Render step of a filled wizard, swap the audio, rename, stop before Render.
cd "${0:A:h}"
e(){ python3 tp_browser.py eval "$1" 2>/dev/null; }
e "(()=>{location.hash='#/create-video';return 1})()" >/dev/null; sleep 4
e "(()=>{const b=[...document.querySelectorAll('button')].find(e=>e.offsetParent&&e.innerText.trim()==='Choose Audio');b.click();return 1})()" >/dev/null; sleep 3
e "(()=>{const b=[...document.querySelectorAll('button')].filter(e=>e.offsetParent&&e.innerText.trim()==='Import Audio');b[b.length-1].click();return b.length})()"; sleep 4
for w in $(seq 1 10); do sleep 2; r=$(e "[...document.querySelectorAll('*')].some(e=>e.offsetParent&&e.children.length===0&&['Audio','$1'].includes(e.textContent.trim()))"); [[ $r == true ]] && break; done
p=$(e "(()=>{const l=[...document.querySelectorAll('*')].find(e=>e.offsetParent&&e.children.length===0&&e.textContent.trim()==='Audio');if(!l)return 'none';const r=l.getBoundingClientRect();return Math.round(r.x+r.width/2)+' '+Math.round(r.y-50)})()" | tr -d '"')
[[ $p == none ]] && echo "already inside a folder"
[[ $p != none ]] && { python3 tp_browser.py clickxy ${=p} >/dev/null 2>&1; sleep 6; }
pos=$(e "(()=>{const l=[...document.querySelectorAll('*')].find(e=>e.offsetParent&&e.children.length===0&&e.textContent.trim()==='$1');if(!l)return 'none';l.scrollIntoView({block:'center'});const r=l.getBoundingClientRect();return Math.round(r.x+r.width/2)+' '+Math.round(r.y-100)})()" | tr -d '"')
echo "card $pos"; [[ $pos == none ]] && exit 1
python3 tp_browser.py clickxy ${=pos} >/dev/null 2>&1; sleep 1
e "(()=>{const b=[...document.querySelectorAll('button')].filter(e=>e.innerText.trim().startsWith('Select'));b[b.length-1].click();return 1})()" >/dev/null; sleep 4
e "[...document.querySelectorAll('*')].filter(e=>e.offsetParent&&e.children.length===0&&/\(mp3\)/.test(e.textContent)).map(e=>e.textContent.trim())"
e "(()=>{const b=[...document.querySelectorAll('button')].filter(e=>e.offsetParent&&e.innerText.trim()==='Next');b[b.length-1].click();return 1})()" >/dev/null; sleep 4
e "(()=>{const i=[...document.querySelectorAll('input')].find(e=>e.offsetParent);i.select();return 1})()" >/dev/null
timeout 30 python3 tp_browser.py fill "input[type=text]" "$2" 2>&1 | tail -1
e "[...document.querySelectorAll('input')].filter(e=>e.offsetParent).map(e=>e.value)"
