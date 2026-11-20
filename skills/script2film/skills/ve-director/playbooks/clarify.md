# Step 1 — Clarify

Ask only for what is missing, numbered, in ONE message. If the user says 「你決定」, use the default column (for 基調, the column says how to pick one).

| Field | Values | Default |
|---|---|---|
| 時長 | 5-10s · 10-15s · 15-30s · 30-45s · 45-75s · 60-90s · 60-180s | ask — it decides the shot count |
| 畫風 (mediaType) | `live` · `3d` · `claymation` · `pixel-art` · `stop-motion` · `comic-book` · `watercolor` · `wool-felt` · `paper-cut` · `ghibli` · `low-poly` · `shadow-puppet`（皮影戲，非官方） | `live` |
| 敘事方式 | 古典細膩（志怪、歷史、古典改編）· 其他 | infer from the idea; say which one you picked |
| 基調 | 未指定 · comedy · warm · action · suspense · horror · romance · uplifting · documentary | not mentioned → 未指定 (follow the idea, never escalate a plain premise into suspense or horror). 「你決定」→ pick the closest of the eight and name it with a one-line reason; if none fits (a tragic or solemn sacrifice has no tone of its own yet), keep 未指定 and say so |
| 比例 | 16:9 · 9:16 | 16:9 |
| 對白 | detected, not asked: spoken lines in the idea → dialogue on, take them literally. Only a title and no text (「把〈種梨〉做成影片」) → still not asked: keep it off and say in one line that the original has spoken lines, which go in only if the user pastes them or asks | off |

Scope of this skill (v0): **storyboard, minimal output only.** If the user asks for single-shot, first-last frame, or a full review document, say this skill does not do that yet and point them to `prompt-studio.html`.

Time of day, weather and season are not asked: decide them in the plan's 世界設定 and list them as assumptions in the CP1 review, so the user can correct them before rendering.

If the user gives a source text (a classical passage, a screenplay excerpt), keep it verbatim: the plan quotes it beat by beat.
If the user gives only a title, never quote the original from memory, in this message or in the plan: tell the story
in your own words, and put a line in quotation marks only when it comes from text the user pasted or a source opened
in this session. A remembered line can be wrong, and the plan's 原文動作 column would carry it as if it were the source.
