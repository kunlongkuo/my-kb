"""vox-host 起手模板（FORMAT.md）：系列模板與每集 make_doc.py 從這份複製後改內容。改稿改這裡再重跑，輸出當前目錄的 doc.json。
示範內容是一集 AI 工具解說的骨架：封面開場（主持人左下圓框）→ 鉤子（VE 現代生活場景）→ 主線場景 → 一句第一人稱觀察 → 主持人出鏡收尾。
複製出去後要改的：L（旁白）、TTS_FIX、beats、shots、doc 的 title／speaker／voice／pip／bgm；配樂 S3 對時後照 FORMAT §4 換成 tools/score 產的 wav。"""
import json, os, sys
from pathlib import Path



def find_s2f():
    """找 PromptStudio：環境變數 S2F_DIR，否則舊名 PROMPTSTUDIO_DIR，否則本檔所在的 PromptStudio，否則上層資料夾裡
    並排的 PromptStudio。只用 os、sys、Path 與 __file__：這份範本在匯入任何東西之前就要找到它。"""
    for name in ("S2F_DIR", "PROMPTSTUDIO_DIR"):
        if os.environ.get(name):
            return Path(os.environ[name])
    here = Path(__file__).resolve()
    found = [p for p in here.parents if (p / "skills/ve-director/doc/scripts/doc_build.py").exists()] + \
            [p / "PromptStudio" for p in here.parents if (p / "PromptStudio/skills/ve-director/doc/scripts").exists()]
    if not found:
        sys.exit("✗ cannot find PromptStudio: set the environment variable S2F_DIR")
    return found[0]


sys.path.insert(0, str(find_s2f() / "skills/ve-director/doc/scripts"))
import doc_lint  # noqa: E402
from doc_build import Q, code, host, tts_lines, ve  # noqa: E402

L = """大家好，歡迎收看工具解說。
今天要講的是：怎麼讓 AI 幫你整理一整週的會議紀錄。
你有沒有開完一週的會，回頭卻找不到上週決定了什麼？
問題不在記性，在紀錄散在五個地方。
第一步，把每場會的逐字稿丟進同一個資料夾。
第二步，請 AI 只抽三件事：決定、負責人、期限。
第三步，每週五把這三欄合成一張表。
我自己這樣做了一個月，開會前終於知道上次講到哪。
以上是我的做法，分享給你。
下一集，我們來講怎麼讓 AI 幫你回信。""".split("\n")
# 破音字：字幕照原文，TTS 改同音字（FORMAT §4）
# 只放這一集才有的唸法（例：阿拉伯數字改成國字、只出現一次的外國人名）。通用的多音字、書卷名、單位名
# 加進 tools/tts/lexicon.json，所有系列都會套用；python3 tools/tts/lexicon.py doc.json 會列出兩邊各換了什麼。
TTS_FIX = {}
beats = [
    code("B1", [1, 2], "cover", {"series": "工具解說", "title": "會議紀錄", "sub": "讓 AI 整理一整週", "sub_at": "怎麼讓",
                                 "badge": "第 1 集", "at": 0.15}),
    ve("B3", 3, "hook_lost"),
    code("B4", 4, "quote_card", {**Q("紀錄散在五個地方", "本集主線", 0.15, 110), "fact": False}),   # 本集主線：講者的話，不進事實清單（FORMAT §9）
    code("B5", [5, 6, 7], "list_reveal", {"title": "三個步驟", "items": [{"text": "逐字稿放同一處", "at": "第一步"},
                                                                    {"text": "只抽三件事", "at": "第二步"},
                                                                    {"text": "週五合成一張表", "at": "第三步"}], "hot": 1}),
    ve("B8", 8, "desk_calm"),
    host("B9", [9, 10]),
]
CAM = "Static wide shot, locked-off, no camera movement."
NOTEXT = "no writing anywhere"
def S(scene_txt, setting, scene, ident, act):
    return {"t2i": [scene_txt, setting], "scene": scene, "ident": ident, "acts": [[0.0, 1.0, act]], "camera": CAM}
shots = {
 "hook_lost": S("A halftone photo cutout of a modern office worker of about thirty in a grey sweater, sitting at a cluttered desk piled with papers and sticky notes, scratching his head, confused.",
   f"Grey and navy torn paper office, cream paper desk lamp light; {NOTEXT}, no logos, no screen visible.",
   "A confused office worker at a cluttered desk of papers and sticky notes", "Preserve the worker, the grey sweater, the papers and the desk",
   "He picks up one paper, frowns and puts it down, in small stop-motion steps."),
 "desk_calm": S("A halftone photo cutout of the same office worker of about thirty in a grey sweater, sitting at a tidy desk with one neat folder, smiling and relaxed.",
   f"Grey and navy torn paper office, cream paper morning light; {NOTEXT}, no logos, no screen visible.",
   "A relaxed office worker at a tidy desk with one folder", "Preserve the worker, the grey sweater, the folder and the tidy desk",
   "He opens the folder and nods, in small stop-motion steps."),
}
# 字幕燒哪一種語言寫在系列的 series.json："subs": {"burn": "zh"}；這一集要和系列不同才在下面的 doc 裡寫同一個鍵
doc = {"title": "會議紀錄", "lang": "zh", "theme": "collage", "speaker": "主持人",
       "voice": {"ref_wav": "refs/host.wav", "ref_text": "refs/host.txt", "seed": 11, "tail_fade": 0.08},
       "gaps": {"default": 0.5, "after": {"2": 0.7, "4": 0.8, "7": 0.8, "8": 1.0, "9": 0.8}},
       "beats": beats, "shots": shots, "facts": "facts.md",   # FORMAT §9 事實清單：facts.md 跟這支腳本放同一個資料夾
       "hook": "反問",   # FORMAT §2 鉤子寫法（反問／反常識／數字／衝突），和上一集不同
       "pip": {"clip": "host/tp_host.mp4", "beats": ["B1"], "crop": [760, 760, 560, 0],
               "d": 310, "ring": "0xf4ecd8", "y": 720, "x": 55},
       "bgm": {"src": "bgm/placeholder.mp3", "lufs": -36, "credit": "本頻道自製（程式作曲）"},   # S3 後換成 tools/score 的 wav
       "sub_bg": {"color": "#000000", "alpha": 0.7},
       "wipes": ["B5"]}
doc["lines"] = tts_lines(L, TTS_FIX)
doc_lint.check(doc)
json.dump(doc, open("doc.json", "w"), ensure_ascii=False, indent=1)
print(len(L), "lines", len(beats), "beats", len(shots), "VE shots")
