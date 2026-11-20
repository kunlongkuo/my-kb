#!/bin/zsh
cd "${0:A:h}"; e(){ python3 tp_browser.py eval "$1" 2>/dev/null; }
pos=$(e "(()=>{const l=[...document.querySelectorAll('*')].find(e=>e.offsetParent&&e.children.length===0&&e.textContent.trim()==='$1');if(!l)return 'none';l.scrollIntoView({block:'center'});const r=l.getBoundingClientRect();return Math.round(r.x+r.width/2)+' '+Math.round(r.y-100)})()" | tr -d '"')
echo "card $pos"; [[ $pos == none ]] && exit 1
python3 tp_browser.py clickxy ${=pos} >/dev/null 2>&1; sleep 1
e "(()=>{const b=[...document.querySelectorAll('button')].filter(e=>e.innerText.trim().startsWith('Select'));b[b.length-1].click();return 1})()" >/dev/null; sleep 4
e "[...document.querySelectorAll('*')].filter(e=>e.offsetParent&&e.children.length===0&&/\(mp3\)/.test(e.textContent)).map(e=>e.textContent.trim())"
e "(()=>{const b=[...document.querySelectorAll('button')].filter(e=>e.offsetParent&&e.innerText.trim()==='Next');b[b.length-1].click();return 1})()" >/dev/null; sleep 4
e "(()=>{const i=[...document.querySelectorAll('input')].find(e=>e.offsetParent);i.select();return 1})()" >/dev/null
timeout 30 python3 tp_browser.py fill "input[type=text]" "$2" 2>&1 | tail -1
e "[...document.querySelectorAll('input')].filter(e=>e.offsetParent).map(e=>e.value)"
