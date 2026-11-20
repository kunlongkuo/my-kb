# Step 2 — Plan (checkpoint CP1)

Read `references/plan-rules.md`, plus the handbook when SKILL.md's table says so. Do not write any T2I or I2V text in this step (plan, machine check and continuity review all happen before CP1): a later step renders each plan row, so every cell must be concrete and decided.

## Output: exactly these six blocks

### 世界設定
One line each: 地點 · 時間 · 天氣/光 · 服裝 · 關鍵道具（含尺寸）. Wardrobes of different Actors share no garment type or colour family (`plan-rules.md` §11).

### 角色
One line per actor: `Actor N` · 名字（the character's proper name from the user's message or source, e.g. 王生、亞倫; `—` if none. A role or kind noun such as 美女、惡鬼、書生、大祭司 is not a 名字: it goes in 身份, and prompts may use it as an appearance word, because VE can draw it, while a proper name means nothing to VE）· 身份 · 是否人類臉（是/否）· 外觀要點（臉、髮、服裝，足以畫肖像）. A character that changes form gets a separate Actor per form. The character's name appears ONLY in this block.

### 空間地圖
Fix the space once, in three parts, before any shot:
- **Boundaries and sides.** Every wall, door, gate or window the story crosses, and which side of it each place is (院牆外 / 院內 / 屋內). For each shot's start, say which side every Actor is on. A character who must cross a boundary to reach the next place cannot already be past it.
- **Camera side.** Which side of each boundary the camera is on, per location (e.g. 牆外的鏡頭在 Actor 1 身後；屋內一律從窗洞看進去).
- **Left/right and depth.** Where things sit in frame and which way people move (畫面左/右, 往畫面深處 / 朝鏡頭). Prefer moves into or out of depth for crossings; side profiles are where motion reverses.

Check the map against the source's own geography (e.g. 「至齋門，門內杜……乃逾垝垣」 = he is outside the study's courtyard gate, and climbs the wall into that courtyard).

### 鏡頭規劃表
| # | 秒數 | 任務 | 原文動作 | 景別 | 構圖與左右位置 | 畫面中的人（臉是否可見） | 開始狀態 | 動作步驟（≤2） | 結束狀態 | 運鏡 | 器物細節 | 聲音（只限畫面內或環境） |

- 任務 = ESTABLISH / APPROACH / WITHHOLD / REVEAL / REACT / ESCALATE / RELEASE.
- 原文動作 = the source beat(s) quoted verbatim, names included; `—` if none. This column and the 原文動作對照 line are for the user's review only — render never copies them into prompts.
- 秒數: integers 3-10, summing inside the requested duration. Shot count from `plan-rules.md` §6: Default column, or Detailed when the handbook says so or when spoken lines need shots of their own (a speaking shot does little else). A speaking shot's seconds come from the line-length table in `dialogue.md`, including its closing beat.
- 開始狀態 / 結束狀態: where each Actor is (which side of which boundary, where in frame) and their pose at the first and last instant. 開始狀態 is exactly what the T2I first frame shows.
- **What counts as one step:** one verb, one body part or object, one end pose. 「舉起人皮、抖一抖、披到身上」 is three steps; 「擲筆」 is one. A shot holds at most two — split the rest into the next shot.
- 景別: one framing per shot. A framing change inside a shot needs a camera move that causes it; a locked-off shot never changes size.
  Exception (experimental): a hard-cut pair, two framings in one generation, only under `plan-rules.md` § FROM 07-experimental.md §1 and in its notation.

Cell rules:
- **Aliases only.** Outside 角色 and the review-only 原文動作 column, name people as `Actor N` — never a character name, not even inside a place name (書齋, not 王生的書齋). Render copies these cells verbatim. Exception: a spoken line is quoted exactly as the source or the user gives it, names and all.
- **Face visibility is binary:** `Actor N（臉可見）` or `Actor N（臉不可見）`. Back view, back of the head, blurred foreground silhouette = 臉不可見; profile or any visible cheek = 臉可見. If a face is visible at any moment of the shot, it is 臉可見.
- **Actor caps.** At most 2 Actors in any one shot (4 is the hard ceiling, with identity-drift risk — `plan-rules.md` § Actor cap); a baby, a child or an animal the story needs on screen is an Actor. When a beat needs more, split it across shots.
- **Closed cast includes body parts.** Any part of an Actor in frame (a hand, a claw, a sleeve) lists that Actor and counts in the head count.
- **First frames are drawable.** 開始狀態 is a held, static pose: standing, crouching, sitting, kneeling, lying, a hand resting on something. Never a pose caught mid-motion (straddling a wall, mid-leap, mid-fall, a foot in the air) — T2I cannot draw it. If the source beat is that motion, start the shot just before it (and let the action happen) or just after it (and let the cut and on-screen evidence — rubble, dust, a muddy hem — tell it).
- **Design actions the model already wants to do.** Given this first frame, what would a video model naturally do next (a person by an opening walks through it; a hand on a door pushes it open)? Stage the space so that natural move is the story's move, instead of writing prohibitions against it. If the natural move is wrong for the story, change the staging, not the wording.
- **Screen direction per shot.** State which way every visible Actor faces or moves (朝畫面右 / 朝畫面左), consistent with the 空間地圖, close-ups included. Positions are always frame-relative (畫面左/右), never a character's own left or right hand.
- **Silent faces act with eyes, brows, head and hands.** A visible face that does not speak in the shot gets no mouth or jaw action (no 咬牙, 下顎收緊, 抿嘴) — render locks that mouth.
- **Verbatim lines that are too long** for one shot's line-length budget are split across shots at a sentence break, never shortened, when the user asked for the source wording.

After the table, two lines:
- `原文動作對照：` every source beat → shot number.
- `連戲檢查：` for each cut, `N→N+1 ✓` or `N→N+1 ✗ <why>`: shot N's 結束狀態 must lead to shot N+1's 開始狀態 — same side of every boundary, same wardrobe and props, positions that a cut can join (an ellipsis is fine if the next 開始狀態 is a place the character could have reached). Fix every ✗ before showing the plan.

### 狀態帳本
A fenced block tagged `ledger`, one line per entity per shot phase, for every Actor in frame and every tracked prop in frame (an entity off-screen in another space needs no line; its next appearance is compared with its last line):

```ledger
S1 開始 | Actor 1 | 院牆外 | 站 | 院門前
S1 結束 | Actor 1 | 院牆外 | 站 | 院門前
S2 開始 | Actor 1 | 院牆外 | 站 | 牆塌陷處前 | 省略：沿牆走到塌陷處
S4 開始 | 彩筆 | 屋內 | 握著 | Actor 2 右手
S4 結束 | 彩筆 | 屋內 | 躺著 | 榻面左側
```
Every difference in 區域, 姿勢 or 所在 between a shot's 結束 and the next shot's 開始 — a stand becoming a crouch included — needs `省略：<reason>`; the check enforces it. Fields: `S<#> 開始|結束 | entity | 區域（which side of which boundary, same words as 空間地圖）| 姿勢或狀態 | 所在（next to what, or in whose hand）| optional 省略：<reason>`. Use the exact same words for the same state across shots — the check compares strings. A change across a cut needs `省略：<reason>` on the next 開始 line; a change inside a shot is fine when the shot's action causes it.

### 導演提案
0-3 ideas that go beyond the source (an added glance, gesture, prop, sound, staging): `提案 N（shot #）：<what> —— <why it helps> —— <what it changes about the story>`. They are NOT in the table. Write `（無）` if none.

## Check, then review, then show

1. Save the six blocks as `plan.md` (see SKILL.md § Files).
2. **Machine check.** Run from the skill directory:
   `python3 scripts/plan_lint.py <absolute path to plan.md> --min <lower s> --max <upper s> --names "<every 名字 in the 角色 block that is not —, comma-separated>"`
   Fix the plan until it exits 0. (No shell: check the same items by reading.)
3. **Independent review.** If you can launch a subagent, give it only `playbooks/continuity-review.md`, `plan.md` and the user's source text or idea, and ask for its output verbatim. Otherwise, re-read the plan yourself strictly as that file describes, as if someone else wrote it. Fix every **阻斷** issue by rewriting the plan as a whole, not by patching single cells: re-read all six blocks, apply the fix, and carry it through every block it touches (空間地圖, every affected row, the ledger, both trailer lines). Leave **次要** issues for the user. Then re-run step 2 and run the review once more (at most two review rounds). At CP1, list every remaining issue — 阻斷 still open and all 次要 — so the user decides.

## Show it to the user

Save exactly the six blocks as `plan.md` (see SKILL.md § Files) — no review text in the file. In chat, show a compact version: the table reduced to `# · 秒 · 任務 · 內容（一句）· 運鏡`, then the 導演提案, then your own review in 2-4 lines (what works, the weakest shot and why), then one line `檢查：plan_lint 通過 · 連戲審查 <通過 | 修正阻斷 N 處：一句話各說是什麼>`, then `次要（未修，請決定）：` one line per 次要 issue, then one line `假設：` listing what you decided that the user did not state (time of day, weather, tone if picked, dynasty-free period cues). End with a numbered choice:

1. 照這份渲染
2. 採用提案 N（可多選）後渲染
3. 修改（指出哪顆、哪一格）

Then STOP and wait. On edits, update `plan.md` and show only the changed rows before rendering.
