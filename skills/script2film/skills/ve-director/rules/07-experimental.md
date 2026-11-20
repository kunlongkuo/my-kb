# 07 — Experimental rules (skill only, not part of the HTML tool)

Rules here are NOT validated on VideoExpress yet. Each one says where it came from and how many takes back it. Use an experimental rule only when it clearly fits; when you use one, say so in one line at CP1 and at delivery so the user knows the shot is a test. Promote a rule into 01/02 only after takes confirm it; delete it if takes refute it.

## §1 Hard-cut pair — two framings in one generation (plan side)

Status: EXPERIMENTAL · 1 test, 3 takes (2026-10-03, watercolor, 中景 → 臉部近景): 2 of 3 cut cleanly, kept face and costume, sound continuous; the cut did not land exactly on the labelled second · idea from an external community VE skill, rewritten here.

**What it is.** One VE generation holds two framings joined by a single hard cut (e.g. 中景 0-4s, then 近景 4-8s). It saves a T2I image and a generation when a beat needs a size change but no camera move.

**Precedence.** For a row that uses it, this suspends the plan rule "one framing per shot; a framing change needs a camera move". Everything else in the plan rules still applies.

**Use it only when all of these hold:**
- **The second framing is a closer view of what the first frame already shows clearly**, from the same camera side and the same screen direction. VE sees only the first frame (the T2I draws 鏡頭一 alone), so anything the second framing shows that the first frame does not show well, it invents.
- **A face close-up after the cut needs that face clearly visible before it**: 鏡頭一 at 中景 (waist up) or closer with the face lit and turned toward camera. 遠景 → 臉部特寫 is out of scope until tested.
- Same place, same Actors, same side of every boundary, no time jump. No Actor appears or leaves at the cut. No reverse angle, no new space.
- Exactly one cut, two sub-shots, each at least 3 s, total 6-10 s. The cut lands near, not on, the labelled second: never time a sound or an action to the exact cut point, and expect about one re-roll in three. At most one action step per sub-shot (the row's two-step cap still holds overall).
- Fits a REACT or REVEAL beat: 中景 of the Actor → 近景 of their reaction; 中景 of the Actor → 特寫 of a prop already lit in their hands or on the table.

**Notation (one table row per generation, so the checks keep working):**
- 秒數: the generation total (e.g. `8`).
- 景別: `中景 0-4s｜硬切｜近景 4-8s`.
- 構圖與左右位置 / 運鏡: one entry per sub-shot, separated by `｜` (e.g. 運鏡 `固定｜固定`).
- 開始狀態 is 鏡頭一's first frame; 結束狀態 is 鏡頭二's last frame. The ledger has the usual two lines; nothing about the entity changes at the cut.
- 任務 gets the suffix `（硬切實驗）`.

## §2 Hard-cut pair — rendering (I2V side)

Status: EXPERIMENTAL, see §1. Applies only to a plan row whose 景別 contains `｜硬切｜`.

**Precedence.** For that row only, these replace parts of the `02-modes.md` §0.1 template:
1. `[REFERENCE USE]`: the image controls 鏡頭一 only. Use: `以提供的圖片作為本次生成的精確開場畫面；它決定鏡頭一的構圖、世界、光線與取景，鏡頭二沿用同一個地點、色調、光線與角色。`
2. `[IDENTITY / CONTINUITY]`: replace `整支為單一連續鏡頭，不剪接。` with `本次生成由兩個鏡頭組成，中間只有一次硬切，依下文順序。` Mouth locks cover every visible face in either sub-shot.
3. The single trailing `[CAMERA]` + `[LIGHT AND IMAGE]` becomes one trio per sub-shot, in this order: `[ACTION 0-<a>s] 鏡頭一。…` `[CAMERA] …` `[LIGHT AND IMAGE] …` `[ACTION <a>-<N>s] 鏡頭二。…` `[CAMERA] 硬切至<景別>：<鏡頭二畫面裡有什麼>，與鏡頭一同一側、同一軸線；…` `[LIGHT AND IMAGE] …`, then `[PRODUCTION SOUND]` and `[NEGATIVES]` once.
4. `[PRODUCTION SOUND]`: add `聲音跨越硬切連續不中斷。`
5. `[NEGATIVES]`: start with `除上述一次硬切外不剪接、` and keep the style's list.

Everything else (語言規則, Actor Alias, locks, the style's `[LIGHT AND IMAGE]` and `[NEGATIVES]`, sound convention) is unchanged. The check script enforces the shape (L8).
