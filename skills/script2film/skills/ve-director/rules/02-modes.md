# Modes

Schema for each mode. Pick one mode from the user's intent (routing rules in `00-operating-manual.md`).

| § | Mode | One-line purpose | Typical duration |
|---|------|------------------|------------------|
| §1 | `storyboard` | multi-shot plan; three output modes (minimal / full / runsheet) | 15-180s |
| §2 | `single-shot` | one T2I + I2V pair | 5-15s |
| §3 | `avatar` | retired 2026-09-19 → storyboard + runsheet | — |
| §5 | `first-last` | one before/after frame pair + transition (VE First Frame Last Frame Beta) | 5-15s |
| §6 | `short-form` | retired 2026-09-19 → 9:16 storyboard, hook in Shot 1 | — |

§4 holds the MediaType bases (`t2iBase` / `motionBase` / `visualLock`) that every mode references.

---

## §0 Output language — write 繁體中文, imitate these

Most templates in these sources, and every official VideoExpress example in `05-ve35-animation-styles.md`, are written in English. **They show structure, not language.** The output of this notebook is always 繁體中文. Only these stay English: the eight uppercase tags (`[REFERENCE USE]` … `[NEGATIVES]`, including `[ACTION 0-2s]` time ranges), `Actor 1` / `Actor 2`, aspect ratios (`16:9`), and camera/lens tokens (`85mm f/1.4`). The quoted dialogue line stays in whatever language the user wrote it in.

### §0.1 繁中 I2V template (fill every `<…>`)

[REFERENCE USE] 以提供的圖片作為本鏡的精確開場畫面；它決定本鏡的構圖、世界、光線與精確取景，地點、色調與攝影機皆沿用該圖。 [IDENTITY / CONTINUITY] 出場角色：<Actor Alias>，<外觀錨點>。畫面中恰好<一｜兩>人。整支為單一連續鏡頭，不剪接。全程保持每位角色的臉、髮型、膚色與服裝和開場畫面完全一致。<每個道具一開始在哪裡，用該 shot T2I 的原字>。開場畫面裡沒有的東西都不會出現：不會冒出新的物件、玩具、車輛、門、家具、動物或人，場景全程是同一個地方。 [SCENE] <取景>，<Actor Alias> 位於 <與開場畫面完全相同的場景佈置>，<光線方向與色調>。本鏡的戲劇重點：<一句話>。 [ACTION 0-<a>s] <一個小幅度的主體動作>。[ACTION <a>-<b>s] <Actor Alias>，<外觀錨點>，says in a <2-word tone>, <Shape A: natural Mandarin accent｜Shape B: natural Taiwanese Mandarin accent>: "<台詞>"。[ACTION <b>-<N>s] <收尾微動作>。 [CAMERA] 只做一種運鏡：<一個有目標的緩慢運鏡>。主體動作與鏡頭運動分開；畫面其餘部分保持穩定。 [LIGHT AND IMAGE] 延續開場畫面的<風格質感>。 [PRODUCTION SOUND] 符合場景的自然環境音（不含任何音樂），持續存在並鋪在台詞之下；無音樂、無旁白，唯一的語音是引號內的台詞。 [NEGATIVES] 避免：<風格的材質失誤>、臉部扭曲、嘴型變形、多餘肢體、形變、閃爍、水印、標誌、慢動作、定格。

A shot with no quoted line drops the speech beat, ends [PRODUCTION SOUND] with 「無音樂、無旁白、不加任何語音」, and adds the mouth lock for every visible face (`01-core.md §11`).

### §0.2 Worked example — one filled shot, the shape to imitate

This is a pattern reference, not content to copy: invent the characters and scene from the user's idea every time.

**Text-To-Image Prompt:** 電影感真人實拍劇照，16:9 寬螢幕，腰部以上。Actor 1，六十歲的台灣母親，圓臉，眼角有細紋，溫和的深棕色眼睛，灰白短髮往後梳，穿深藍色開襟毛衣、內搭米色棉質上衣，坐在舊公寓廚房的木餐桌後方偏畫面左側，腰部以上入鏡，身體微朝右，雙手捧著一只冒著熱氣的白瓷湯碗放在桌面上，視線望向畫面右側。未修飾的皮膚質感，毛孔清晰可見，臉部自然不對稱，不磨皮、不美顏。她身後左側是淡綠色磁磚牆與老式瓦斯爐，右側是半掩的木門，門外走廊一片昏暗。一盞暖黃色鎢絲燈泡從正上方打下，在桌面投下柔和的圓形光池，她的臉一側落入陰影。色彩如未調色的 RAW 原片，細微的感光元件顆粒，焦點落在她臉上、景深淺。安靜、等待的深夜氛圍。無文字、無水印。

**Image-To-Video Prompt:** [REFERENCE USE] 以提供的圖片作為本鏡的精確開場畫面；它決定本鏡的構圖、世界、光線與精確取景，地點、色調與攝影機皆沿用該圖。 [IDENTITY / CONTINUITY] 出場角色：Actor 1，灰白短髮、深藍開襟毛衣的六十歲台灣母親。畫面中恰好一人。整支為單一連續鏡頭，不剪接。全程保持她的臉、髮型、膚色與服裝和開場畫面完全一致。白瓷湯碗一開始在她雙手之間的桌面上。開場畫面裡沒有的東西都不會出現：不會冒出新的物件、玩具、車輛、門、家具、動物或人，場景全程是同一個地方。 [SCENE] 腰部以上，Actor 1 坐在舊公寓廚房的木餐桌後，暖黃燈泡從正上方打光。本鏡的戲劇重點：她把熱湯推給剛進門的女兒。 [ACTION 0-2s] Actor 1 雙手把湯碗緩緩推向畫面右側。[ACTION 2-6s] Actor 1，灰白短髮的母親，says in a warm, gentle natural Mandarin accent: "先喝口熱湯吧。"[ACTION 6-8s] 她收回雙手放在桌緣，眼神仍望向畫面右側，湯碗上的熱氣緩緩上升。 [CAMERA] 只做一種運鏡：極緩慢推向她的臉，嘴部全程完整在框內。主體動作與鏡頭運動分開；畫面其餘部分保持穩定。 [LIGHT AND IMAGE] 延續開場畫面的真人實拍攝影質感。真實材質紋理、自然動態模糊，無 CGI 光澤。 [PRODUCTION SOUND] 老冰箱低沉的運轉聲與遠處的夜間車聲，持續存在並鋪在台詞之下；無音樂、無旁白，唯一的語音是引號內的台詞。 [NEGATIVES] 避免：CGI 或 3D 渲染感、塑膠光澤、過度平滑的數位潔淨感、臉部扭曲、嘴型變形、多餘肢體、形變、閃爍、水印、標誌、慢動作、定格。

❌ `[ACTION 2-6s] Actor 1, the mother, says gently: "先喝口熱湯吧。"` — English body around a Chinese line.
❌ `[SCENE] Waist-up of Actor 1 at the kitchen table, warm overhead light.` — any English sentence in a prompt body.
✅ The two prompts above: 繁中 everywhere except the tags, `Actor 1`, `16:9`, and the speech-act wrap `says in a <tone>, <accent>: "<line>"`, which stays English in every language: ve-runner finds spoken lines only by that wrap (a 繁中 `以…語氣說：` wrap made a 2026-11-19 film's speaking shots render silent), and the line inside the quotes keeps its own language.

---

## §1 storyboard

Full multi-shot video plan with character continuity and timestamps. Used for VideoExpress when the user wants a complete production-ready storyboard.

### §1.1 Storyboard Hard Constraints (Tier 1)

- Output must contain ALL required headings in the exact order listed in Output Format.
- Timestamps must be continuous with zero gaps. Format: `00:00-00:05`.
- No single shot duration exceeds 10 seconds.
- **Total runtime must land inside the user-selected duration** — choose shot count and per-shot seconds so they sum into that range (`01-core.md §6`).
- **ONE primary action beat per shot.** If describing what happens needs more than one sentence, split it into two shots (`01-core.md §7`).
- **Size each spoken line to its shot's seconds** — ~2 spoken words per second, tighter for 中文 per `01-core.md §3`. A shot that speaks does little else.
- **Freeze the world's facts across shots**: location, time of day, weather, wardrobe, props and their scale stay identical unless the user asked otherwise or the plan declares an arc up front. Only the wording, framing, action and cited traits vary (`01-core.md §9`). A time-of-day progression is decided during clarify, never improvised per shot.
- **Scale-lock every prop with a wide size range** — numeric dimension, downgraded modifier, surface plus hand anchor, size token repeated in every shot the object appears (`01-core.md §8`).
- Speaking shots use close-up to waist-up framing. Non-speaking shots may widen slightly but central subject stays readable.
- If `dialogue = true`: per-shot quoted dialogue ≤ 120 characters; split longer lines into multiple shots. Wrap as speech act per `01-core.md §3`. **NEVER use character Name in T2I / I2V prompt bodies — Actor Alias only.**
- If `dialogue = true`: vary the `<tone>` adverb across shots to avoid monotone delivery.
- If `dialogue = false`: prefer no dialogue. Any unavoidable line is short and isolated to one stable shot.
- **No burned-in text, by default and without asking** (`01-core.md §10`): dialogue only ever appears inside a speech-act wrap; the words subtitle / caption / lower third / text overlay / 字幕 never appear in a prompt, not even negated; genre tokens that drag captions along (news broadcast, TikTok, kinetic typography) are replaced by physical staging; text-bearing objects stay out of frame or are specified blank. Use positive cleanliness tokens instead: unmarked frames, plain unbranded surfaces, uncluttered compositions.
- Apply universal avoidances per `01-core.md §5`.

### §1.2 Storyboard Output Format

Storyboard has three output modes (`01-core.md §4`). **`minimal` is the default** and is specified here; `full` is §1.2b and `runsheet` is §1.2c. Emit the sections of exactly one output mode.

### §1.2a minimal (DEFAULT) — paste-ready

Required sections in this exact order:

1. `# Actor Portrait Image Descriptions`
2. `# Scenes, Storyboard And Generation Prompts` (N shots)

NO other sections. NO Name field anywhere — Actor Alias only.

#### Actor Portrait section

Per recurring actor, emit one detailed paragraph hitting **8-10 descriptive dimensions**. A 4-5 dimension portrait is too thin — VideoExpress relies on rich actor portraits to stabilize identity. Default template:

```
Actor N: <t2iBase> of a <age>-year-old <ethnicity / nationality> <gender + role>, <facial feature 1>, <facial feature 2>, <skin / complexion>, <hair style + color>, wearing <clothing top> <fabric / color>, <held object if applicable e.g. "holding a small black wireless handheld microphone near her chest">, <framing — for talking-head use literal "framed from head to waist">, <hands visible note when natural>, <angle — "front-facing three-quarter angle" or "three-quarter angle">, <background>, <lighting — e.g. "soft city street daylight" / "warm practical café lighting" / "dimly lit studio with warm accent lighting">, shallow depth of field, wide <aspectRatio> composition, clean unmarked background, plain unbranded surfaces.
```

Example (talking-head reporter, from VideoExpress dogfood):

> Actor 1: Cinematic medium shot portrait with highly detailed natural facial features of a 28-year-old female Taiwanese news reporter, professional and approachable, clear expressive eyes, light olive skin texture, styled shoulder-length dark hair, wearing a sleek navy blue blazer over a cream blouse, holding a small black wireless handheld microphone near her chest, framed from head to waist, front-facing three-quarter angle, soft city street daylight, shallow depth of field, wide 16:9 composition.

Example (street pedestrian, same source):

> Actor 2: Cinematic medium shot portrait with highly detailed natural facial features of a 34-year-old Taiwanese male pedestrian, realistic skin texture with slight stubble, expressive dark brows, neat short black hair, wearing a casual gray linen button-up shirt, hands visible near hips, clear and slightly thoughtful eyes, three-quarter angle, background of a bustling Taipei street, soft practical lighting, shallow depth of field, wide 16:9 composition.

Counted dimensions in those examples: 8-11 each. Avoid emitting 4-5 dimension portraits like `Actor 1: ... female reporter, microphone in hand, chest-up view, stable composition, clear expressive face, clean unmarked background.` — that's too thin for VideoExpress to lock identity reliably.

This paragraph IS the Continuity Anchor referenced in subsequent shots (per `01-core.md §2`). Since 2026-09-20 it follows the T2I Shape below with two portrait changes: movement 1 is a three-quarter waist-up pose facing the viewer with both hands visible and the complete face / hair / wardrobe inventory; movement 2 is a plain, solid, muted-colour studio backdrop with no props (a plain background keeps burned-in text at zero, `04-platform-videoexpress.md`).

#### T2I Shape (every Text-To-Image prompt, all modes except first-last)

The official v3.5 T2I examples (`05-ve35-animation-styles.md §3`) are long prose in four movements; a comma-list of slots produces 70-word keyword salads that VideoExpress renders flat. Write each T2I as ONE paragraph with no line breaks, 150-250 words (200-350 字 in 繁體中文 output), in this order:

1. **Opener + subject.** The literal opener `<t2iBase>, widescreen 16:9, <shot size: full body | waist-up | close-up>.` (vertical 9:16 for shorts; the size clause is always the third clause), then `Actor N, <continuity anchor>` — the face feature by feature (eye shape and colour, brows, nose, mouth, skin, hair), the wardrobe layer by layer, then a STATIC pose: position in frame (left / centre / right), crop (full body / waist-up / close-up), body angle, gaze direction, what each hand is doing. On live shots with a visible face, the faceLock sentence sits here (`01-core.md`).
2. **Environment with placement.** Every named object gets a position — on the left, behind, upper right, lower-left foreground. One subject, one layer: no mirrors, screens or picture-in-picture (`01-core.md` drawability rules).
3. **Light, material, mood.** Light source and direction, the shadow it casts, the style's material lock woven into prose (`05 §2` t2iBase / visualLock vocabulary), then a one-phrase mood.
4. **Closer.** The literal sentence `No text or watermark.` (`無文字、無水印。`).

Never emit slot names, a comma list of keywords, or the legacy suffix `aspect ratio, clean unmarked frame`. Use the `05 §3` examples as pattern references only — new character and scene from the brief every time.

#### Shot plan across the storyboard (2026-09-20)

The official v3.5 examples move the camera in every shot — nine slow pushes and one backward tracking move, each naming its target and what stays in frame. Across a storyboard: use at least three shot sizes (wide / full body, medium / waist-up, close-up / chest-up), never one size for three shots in a row (prefer a size change on every cut), tightest framing on the emotional peak, and state the size in movement 1 of every T2I. Every shot's `[CAMERA]` is one slow targeted move (`slow push toward the girl's face, retaining her hands and the crouched wolves in frame`); consecutive shots never share the same move; speaking shots default to a very slow push toward the speaker's face with the mouth fully in frame, and `locked off` is allowed on at most one speaking shot per storyboard, never twice in a row. No orbit, handheld, whip pan or zoom-and-pan combos. Plan the sequence first — a six-shot plan reads: full body (push toward the character) → waist-up (drift past the table) → close-up (push toward the face) → waist-up (pull back) → full body (drift) → close-up (push toward the hands); a two-person dialogue still alternates waist-up two-shot and close-up on the speaker rather than holding one framing.

#### Multi-character scenes (2026-09-21)

"One layer of reality per frame" forbids reflections and picture-in-picture, not a second character — a two-shot is wanted. When two or more actors share a scene: write one Scene Lock sentence (location, time of day, light source and direction, palette) and repeat it verbatim in movements 2-3 of every T2I and in `[SCENE]` of every I2V, so the actors never end up under different skies; include at least one two-shot with both actors placed left / right and their distance stated, whose I2V moves exactly one of them; fix screen direction for the whole scene (who faces right, who faces left) and state it in every single-actor shot; put part of the opponent in the near foreground of reaction shots; never render contact — the strike travels toward the frame edge in one shot and the recoil, with the striker's limb in the foreground, is the next. Non-human actors get a full-body three-quarter portrait, not waist-up.

#### Per-shot format

Use `## Shot N` H2 + bulleted fields (NOT a table). Exactly four bullets, in order:

- `**Time:** 00:00-00:06`
- `**Duration:** 6s`
- `**Text-To-Image Prompt:** <one paragraph in the T2I Shape above — the Actor Alias plus the portrait's continuity anchor, staged in THIS shot's setting, pose and framing; mouth visible on dialogue shots>`
- `**Image-To-Video Prompt:** [REFERENCE USE] Use the supplied image as the exact opening frame; it controls the composition, the world, the lighting and the exact framing of this shot, and the location, palette and camera come from it. [IDENTITY / CONTINUITY] Characters present: <Actor Alias>, <continuity anchor>. Exactly one continuous shot, no cuts. Keep every character's face, hair, skin tone and wardrobe identical to the opening frame for the whole shot. [SCENE] <framing> of <Actor Alias> in <setting exactly as staged in the frame>, <light direction and colour>. The dramatic beat of this shot: <one line>. [ACTION 0-<a>s] <ONE small subject motion>. [ACTION <a>-<b>s] <speech-act wrap per 01-core.md §3 if dialogue, otherwise the next single motion>. [ACTION <b>-<N>s] <closing micro-action, then hold>. [CAMERA] One move only: <slow push toward <target>, retaining <what must stay in frame> | slow pull back from <target> | slow lateral drift past <target>; speaking shots may be locked off>. Subject motion and camera motion are separate; hold the rest of the frame steady. [LIGHT AND IMAGE] Continue the exact lighting, colour grade and <style look, 05-ve35-animation-styles.md §2> of the opening frame. [PRODUCTION SOUND] Natural scene ambience matched to the location, present and continuous; no music, no narration, <no added speech | the only speech is the quoted line>. [NEGATIVES] Avoid: <style negatives, 05 §2>, distorted faces, warped mouths, extra limbs, morphing, flicker, on-screen text, captions, watermarks, subtitles, logos, slow motion, frozen frames.`

The I2V line follows the VideoExpress v3.5 eight-tag grammar (`05-ve35-animation-styles.md §1`): tags are literal uppercase and stay English even in 繁體中文 output; one motion per `[ACTION]` segment, segments contiguous over the shot duration (a single-beat shot uses one `[ACTION 0-Ns]`).

Timestamps continuous with zero gaps across consecutive shots.

#### Shot duration & I2V time-split (calibrated from VideoExpress native generator)

Shot duration is **5-9s, picked by content — DO NOT lock all shots to the same duration**:

- **5-6s** — pure action shot, no dialogue, simple beat
- **8s** — single dialogue line + lead-in action + closing micro-action
- **9s** — multi-beat dialogue + interaction + closing micro-action
- **HARD CAP: 10s per spot** (VideoExpress platform limit)

A storyboard of 6 shots that are ALL 8s is a code-smell — it means you defaulted instead of picking by content. Mix durations: e.g. `6s / 8s / 8s / 9s / 8s / 9s` for a dialogue-heavy interview.

#### I2V time-split — closing micro-action buffer (Shape A required, Shape B optional)

**Critical (2026-05-20 dogfood learning):** in **Shape A (Narrative)** content, when dialogue occupies the absolute final beat with no buffer after, the video model often fills the leftover time with an unwanted **sigh / breath / shrug**. Solution: dialogue is the **second-to-last beat**, with a short **closing micro-action beat (0.5-1s)** explicitly specified.

In **Shape B (Talking-Head Reporter)**, the closing buffer is **optional** — host holding professional eye contact on camera after dialogue is the model's default behavior. VideoExpress's native talking-head generator routinely emits dialogue in the absolute final beat (e.g. `[4-8] seconds: ... says in an informative, engaging Taiwanese Mandarin accent: "..."`) without sigh artifacts. See `04-platform-videoexpress.md Content shape detection` to decide which shape applies.

**Shape A dialogue beat structure** (dialogue in second-to-last beat + closing micro-action):

| Shot length | Beats | Example structure |
|-------------|-------|-------------------|
| 6s | 3 beats | `[0-2]` lead-in + `[2-5]` dialogue (3s) + `[5-6]` closing micro-action (1s) |
| 8s | 4 beats | `[0-2]` lead-in + `[2-4]` preparation + `[4-7]` dialogue (3s) + `[7-8]` closing micro-action (1s) |
| 9s | 4 beats | `[0-2]` lead-in + `[2-4]` preparation + `[4-8]` dialogue (4s) + `[8-9]` closing micro-action (1s) |

**Shape B dialogue beat structure** (dialogue in final beat is fine):

| Shot length | Beats | Example structure |
|-------------|-------|-------------------|
| 6s | 3 beats | `[0-2]` lead-in + `[2-4]` preparation + `[4-6]` dialogue (2s, ~10-15 字) |
| 8s | 3 beats | `[0-2]` lead-in + `[2-4]` preparation + `[4-8]` dialogue (4s, ~30-40 字) |
| 9s | 3 beats | `[0-2]` lead-in + `[2-4]` preparation + `[4-9]` dialogue (5s, ~35-45 字) |

**Non-dialogue shot beat structure** (no closing buffer needed):

| Shot length | Beats | Example structure |
|-------------|-------|-------------------|
| 5s | 2 beats | `[0-2]` + `[2-5]` |
| 6s | 3 beats | `[0-2]` + `[2-4]` + `[4-6]` |
| 8s | 3 beats | `[0-2]` + `[2-4]` + `[4-8]` |
| 9s | 3 beats | `[0-3]` + `[3-6]` + `[6-9]` |

Each beat is 1.5-4 seconds of one sub-action. **Avoid 5-second beats.**

**Closing micro-action examples** (the 0.5-1s beat right after dialogue):

- `[7-8 seconds]: Actor 1 holds steady eye contact with the camera as the moment settles.`
- `[7-8 seconds]: Actor 1 closes her mouth gently, maintaining a professional posture.`
- `[8-9 seconds]: Actor 2 holds his thoughtful expression, hands still on the table.`
- `[7-8 seconds]: Actor 1 maintains her engaging smile, the city lights softly glowing behind her.`

**Anti-pattern (causes sigh / breath filler):**

- `[4-8 seconds]: ... and says in a warm, peaceful natural Mandarin accent: "上帝會一直保護我們。"` ← dialogue is final beat, no buffer; model auto-generates sigh in remaining ~1s

**Correct (calibrated):**

- `[4-7 seconds]: ... and says in a warm, peaceful natural Mandarin accent: "上帝會一直保護我們。"` 
- `[7-8 seconds]: Actor 1 holds her warm gaze on her daughter, gentle bedside lamp light flickering softly.`

#### T2I boilerplate

**Retired 2026-10-01.** The old rule "every T2I includes the literal English phrase `stable composition, clear expressive face`" is withdrawn: it contradicts §0 (prompt bodies are 繁體中文) and is wrong on shots where no face is visible. The four-movement T2I shape already carries the stability; do not add the phrase. For a dialogue shot, state in Chinese that the speaker's mouth is fully visible in frame.

#### Continuity Anchor per shot

Per `01-core.md §2`, use the **short form** of the Continuity Anchor inside per-shot T2I and I2V — `Actor 1, the elderly watchmaker with wire-rimmed glasses` is sufficient. **Vary which 1-2 traits get cited across shots** (paraphrase the short form), but keep Actor Alias + age range identical. Do NOT repeat the full Character Bible / Actor Portrait paragraph inside every shot — that's redundant noise.

#### Framing keyword

**Default framing family** — use one of these framing words plus the literal suffix **`maximum`** when it specifies the closest-allowed framing for that shot:

- `close-up maximum`
- `medium close-up` (no maximum suffix; this is the loosest VideoExpress-friendly framing)
- `chest-up maximum`
- `waist-up maximum`

Framing CAN vary across shots within this family.

**Extended framing family** (Shape A Narrative drama only — Shape B Talking-Head stays locked to its literal framing string per `04-platform-videoexpress.md`):

- `worm's-eye view` · `god's-eye top-down` · `aerial drone perspective` · `over-the-shoulder` · `first-person POV` · `orbital camera` · `handheld tracking` · `full-body wide framing`

These were originally banned but 2026-05-24 dogfood validated all of them at 65-85 quality scores when written with the **Director Gaze framework** (three director questions + numerical spatial parameters + subject-camera gaze rule + actor pose lock + time-bound motion). See `04-platform-videoexpress.md § Director Gaze framework` before using any of these — bare keyword usage without framework under-renders to 50-60. NEVER use these in Shape B Talking-Head storyboards (interview/reporter/podcast).

Do NOT use `macro` or `dolly zoom` as bare keywords — these remain unvalidated.

### §1.2b full — review structure

Emitted only when the user asks for 完整版 / full / 分鏡表 / character bible / review 結構. All shot-level craft rules from §1.2a still apply; only the surrounding sections differ.

Required sections in this exact order:

1. `# Project Snapshot` — Title | Logline | Genre | Target Duration | Aspect Ratio | Visual Style | Emotional Theme | Ending
2. `# Creative Assumptions` — brief bullets on setting, tone, characters, duration, visual style
3. `# Character Bible` — one row per character: Name | Actor Alias | Role | Age | Physical | Clothing | Personality | Want | Voice | Lipsync (dialogue only) | Continuity Anchor
4. `# Emotional Arc` — Beat | Timestamp Range | Emotion | What Changes
5. `# Storyboard And Generation Prompts` (N shots) — Shot | Time | Duration | Purpose | Dialogue (dialogue only) | Text-To-Image Prompt | Image-To-Video Prompt | Lipsync Notes / Performance Notes
6. `# Dialogue Script` (dialogue only) — Time | Actor Alias | Name | Line | Delivery | Lipsync Notes
(Sections 7 `# Continuity Lock Prompt` and 8 `# Optional Negative Prompt` were retired 2026-09-19: per-shot `[IDENTITY / CONTINUITY]` and `[NEGATIVES]` in the v3.5 I2V grammar replace them.)

**Name vs Actor Alias**: Name appears ONLY in the review-facing sections (Character Bible, Emotional Arc, Dialogue Script). Every T2I / I2V prompt body still uses Actor Alias + continuity anchor, exactly as in minimal mode.

In full mode the storyboard is a markdown table (one row per shot). In minimal mode it is `## Shot N` headings with bullets. Do not mix the two.

### §1.2c runsheet — VideoExpress execution run sheet

Emitted when the user says 執行工單 / run sheet / 要給 agent 跑 / 我要一幕一幕貼進 VE. Calibrated from a real end-to-end VideoExpress run (2026-08-08): character image → lipsync clips → timeline → FullHD export.

This output mode routes fields differently from every other mode, because VideoExpress's lipsync generator takes **three separate inputs** and mixing them breaks the render:

| VE field | Carries | Never carries |
|----------|---------|---------------|
| Image Prompt | the frozen Character Bible paragraph + this scene's expression clause | dialogue text |
| Lipsync Video Prompt | one director's note naming the actor and the delivery emotion | dialogue text |
| Actor 1 Script | the spoken line, under 100 characters | anything else |

Speech placed anywhere but the Actor 1 Script field renders as a **closed-mouth narration**.

Required sections in this exact order:

1. `# Character Bible`
2. `# Voice Direction` (dialogue only)
3. `# Scene Run Sheet` (N scenes)
4. `# VideoExpress Settings Checklist`
5. `# How To Run`

#### `# Character Bible` (runsheet)

One frozen paragraph of 40-70 words per recurring character (usually ONE):

`Actor N: A [AGE]-year-old [gender], [build], [skin tone], [hair colour + length + style], [one facial detail], wearing [EXACT garment + plain colour word], [seated/standing] in [single location] with [ONE background object + position], [lighting direction + quality], shallow depth of field, shoulders-up framing, camera at eye level, static camera.`

- Age as a number (`34-year-old`, not a range). Garment colours as plain words (`charcoal-grey`, not `slate ombré`). One location noun. One background object with position.
- The paragraph is **FROZEN**: re-paste it byte-identical into every scene's Image Prompt. Never shorten it, never paraphrase it, never write `same person as before` — the generator has no memory between scenes, and one changed word produces a different face.
- `Actor 1`, `Actor 2`, ... in appearance order. VideoExpress's own lipsync dialog addresses "Actor 1", so the alias doubles as the platform's native actor reference.

#### `# Voice Direction` (dialogue only)

One line, reused identically in every scene:

`Neutral American English accent, warm confident tone, natural conversational pace.`

#### `# Scene Run Sheet` (N scenes)

Each scene is one independent ~8-second clip. **No cross-scene timestamps and no scene-to-scene references** — the bible carries all continuity.

Tag every scene with ONE dominant emotion (Shocked / Angry / Sad / Surprised / Excited / Happy; Curious / Relieved as connectors). No two consecutive scenes share an emotion; flip polarity (negative ↔ positive) at least 3 times when there are 5+ scenes. Scene 1 names the stakes; the final scene resolves the open loop on the highest-energy positive beat.

Per scene emit `## Scene N — [Emotion]` plus exactly these fields, in order:

- `**Image Prompt:**` the ENTIRE Character Bible paragraph verbatim, then one new action/expression clause carrying this scene's emotion. Face and upper body only — no standing up, no walking, hands stay out of frame.
- `**Lipsync Video Prompt:**` (dialogue) one line naming the actor and directing delivery like a film director, e.g. `Actor 1 is the [brief visual tag]. He says his line in a [emotion] tone.` No dialogue text here.
- `**Actor 1 Script:**` (dialogue) the spoken line, UNDER 100 characters including spaces and punctuation — the platform rejects longer. Append the count, e.g. `(74 chars)`.
- `**Video & Audio Prompt:**` (no-dialogue projects, replaces the two fields above) motion and ambience direction only — subtle head/eye movement, breathing, environment sound. No speech, no quoted text.

Framing for the whole run sheet: close-up to shoulders-up, camera at eye level, static camera, hands out of frame, no props, one background object only. Close-up framing is what gives VideoExpress its best character consistency.

#### `# VideoExpress Settings Checklist`

Emit verbatim; the executor re-verifies every item before EVERY generation:

- Generator card: "Create Video From Prompt" (badges: Image to Video, Lipsync HD, Narrate, Consistent Character)
- Aspect: [Landscape 16:9 / Vertical 9:16] — the selector INSIDE the generator modal, not the preview-canvas one
- Image Type: human
- Use Consistent Character: ON — reference photo in slot 1, slot 2 EMPTY
- Advanced Mode → Manual Video Length: 8s (set duration FIRST — ticking Lipsync hides the length controls; actual clip length follows the audio)
- Lipsync HD Video: ON — speech goes ONLY in the Actor 1 Script field of the Create Lipsync Audio dialog that opens AFTER clicking Create Video; dialogue anywhere else renders a closed-mouth narration. (OFF for no-dialogue projects.)
- "Automatically enhance my image prompt": OFF after the hero image is saved — the enhancer rewrites the bible and breaks identity
- "Share this in the public gallery": OFF — re-verify after every modal reopen
- Max 5 generations in parallel; poll the "My AI Videos" folder for completion
- Media tile captions equal the prompt text — use them to match clips to scenes when ordering the timeline

#### `# How To Run`

Emit verbatim:

- Agent execution: give this run sheet to a browser-capable agent (Claude in Chrome / Claude Code / ChatGPT agent mode) together with the official VideoExpress agent workflow: https://github.com/strontiumplatform/VideoExpress.ai-Full-Length-Consistent-Character-Realistic-Talking-Avatar-Video-Workflow — this run sheet REPLACES the workflow's own script-and-bible-writing step (its STEP 1); every other step still applies.
- Manual execution: apply the settings checklist once, then copy-paste each scene's fields into VideoExpress scene by scene, re-verifying the checklist before each generation.

**Known platform behaviour** (2026-08-08 real run): actual clip length is decided by the audio, so an 8s setting yields 4.5-6s clips with very little dead air. The platform's own video-prompt enhancer rewrites prompts into `[0-4.5] seconds: ...` segments — the same timing syntax this knowledge base uses, which is why it survives enhancement.

### §1.3 Storyboard Silent Quality Checks

Run these mentally before emitting; never print them.

All output modes:

- ✓ Exactly the sections of ONE output mode present, in order, exact spelling — no headings from another output mode
- ✓ Shot / scene count matches the user-selected duration per `01-core.md §6`, and per-shot seconds sum into that range
- ✓ Shot duration limit (≤ 10s per clip) satisfied
- ✓ One primary action beat per shot; spoken lines fit their shot's seconds (~2 words/second)
- ✓ Dialogue character limit satisfied if dialogue (≤ 120 chars per shot; ≤ 100 chars per Actor 1 Script in runsheet)
- ✓ Location, time of day, weather, wardrobe and props read as one continuous reality across shots — only the wording varies, unless a declared arc changes a fact
- ✓ Every prop with a wide size range carries a numeric size token plus a surface or hand anchor, repeated in each shot it appears
- ✓ Subtitle suppression rule satisfied
- ✓ Output contains no conversational intro or meta-commentary

minimal / full:

- ✓ Timestamp continuity verified (zero gaps across consecutive shots)
- ✓ T2I / I2V prompt bodies reference characters by Actor Alias + continuity anchor — Names appear only in full mode's review sections, never in minimal

runsheet:

- ✓ Character Bible paragraph appears byte-identical in every scene's Image Prompt
- ✓ No dialogue text inside any Image Prompt or Lipsync Video Prompt
- ✓ Every Actor 1 Script is under 100 characters, with the count appended
- ✓ The Voice Direction line is identical wherever voice is referenced
- ✓ Emotion tags: exactly one per scene, no two consecutive scenes share one
- ✓ Settings Checklist and How To Run blocks emitted verbatim

---

## §2 single-shot

ONE production-ready shot: a T2I + I2V pair. Used for VideoExpress short / fast prompts.

### §2.1 Single-Shot Hard Constraints

- Output exactly ONE shot. No multi-shot lists or storyboards.
- Shot duration must fit the user-selected duration; a single generated clip stays ≤ 10 seconds regardless. If the user asked for more than ~15 seconds, say that `storyboard` fits better before generating.
- Speaking shots: close-up to waist-up. Otherwise medium framing allowed if subject readable.
- No intentional text/UI/labels in frame.
- Apply universal avoidances per `01-core.md §5`.
- If `dialogue = true`: ≤ 120 chars, wrap as speech act per `01-core.md §3`.

### §2.2 Single-Shot Output Format

Emit EXACTLY these two blocks. No "Shot Brief", no sub-fields, no intro text.

```
### Text-to-Image Prompt
<one paragraph in the T2I Shape (§1.2a) — the subject is whatever the brief names; a person gets a short visual anchor, an empty scene has no people; mouth visible if dialogue>

### Image-to-Video Prompt
[REFERENCE USE] Use the supplied image as the exact opening frame; it controls the composition, the world, the lighting and the exact framing of this shot, and the location, palette and camera come from it. [IDENTITY / CONTINUITY] Characters present: <subject>, <short visual anchor if human>. Exactly one continuous shot, no cuts. Keep every character's face, hair, skin tone and wardrobe identical to the opening frame for the whole shot. [SCENE] <framing> of <subject> in <setting exactly as staged in the frame>, <light direction and colour>. The dramatic beat of this shot: <one line>. [ACTION 0-<a>s] <ONE small subject motion>. [ACTION <a>-<b>s] <speech-act wrap per 01-core.md §3 if dialogue, otherwise the next single motion>. [ACTION <b>-<N>s] <closing micro-action, then hold>. [CAMERA] One move only: <slow push toward <target>, retaining <what must stay in frame> | slow pull back from <target> | slow lateral drift past <target>; speaking shots may be locked off>. Subject motion and camera motion are separate; hold the rest of the frame steady. [LIGHT AND IMAGE] Continue the exact lighting, colour grade and <style look, 05-ve35-animation-styles.md §2> of the opening frame. [PRODUCTION SOUND] Natural scene ambience matched to the location, present and continuous; no music, no narration, <no added speech | the only speech is the quoted line>. [NEGATIVES] Avoid: <style negatives, 05 §2>, distorted faces, warped mouths, extra limbs, morphing, flicker, on-screen text, captions, watermarks, subtitles, logos, slow motion, frozen frames.
```

One line, eight v3.5 tags in order (`05-ve35-animation-styles.md §1`). `[ACTION]` segments follow the dynamic time-split per shot duration (same as storyboard `§1.2a`). Do NOT prefix with `Animate this image into a [duration]-second...` boilerplate. Do NOT trailing-append `Animate natural lipsync...` after speech-act wrap.

### §2.3 Single-Shot Silent Quality Checks

- ✓ Exactly one shot (no multi-shot list)
- ✓ Shot duration within platform durationRange
- ✓ Framing satisfied
- ✓ Output contains no meta-commentary

---

## §3 avatar (retired 2026-09-19)

Retired. A single speaker talking to camera is a `storyboard` in `runsheet` output mode: the Character Bible is frozen, every scene re-pastes it, and the spoken line goes in the Actor 1 Script field (`§1`, `04-platform-videoexpress.md`). Section number kept so cross-references stay valid.

---

## §4 MediaType bases (referenced by all modes)

The T2I / I2V patterns reference three slots: `<t2iBase>`, `<motionBase>`, `<visualLock>`. `<visualLock>` is **subject-aware** — pick the variant matching the shot's main subject so identity-preservation tokens stay on-topic.

### §4.1 Bases (same across subjects)

| MediaType | `<t2iBase>` | `<motionBase>` |
|-----------|-------------|----------------|
| `live` | `Cinematic live-action film still` | `cinematic live-action shot` |
| `3d` | `Cinematic 3D animated film still` | `cinematic 3D shot` |
| `2d-animation` | `2D animated film still` | `2D animated shot` |
| `illustration` | `Editorial illustration still` | `subtle ambient illustrated shot` |

### §4.2 visualLock variants (pick per shot's main subject)

**visualLock contains identity + technical-quality tokens ONLY. It does NOT include lighting tokens — lighting is filled by the per-shot `<lighting>` slot in the T2I template (e.g. `warm dim café lighting`, `dimly lit studio with blue and orange ambient lights`).** Mixing lighting into visualLock causes duplicate tokens like `..., authentic lighting, realistic human identity, authentic lighting, ...`.

| MediaType | Human subject | Product / object subject | Human + product mixed |
|-----------|---------------|--------------------------|------------------------|
| `live` | `realistic human identity, unretouched skin texture with visible pores and natural facial asymmetry, natural color like an unedited RAW frame, fine sensor grain, NO skin smoothing, NO beauty filter, NO waxy CGI look, clean frame` | `product identity preserved, material consistency, accurate proportions, natural color like an unedited RAW frame, fine sensor grain, NO CGI or 3D-render look, clean frame` | `realistic human identity, unretouched skin with visible pores, product identity preserved, material consistency, fine sensor grain like an unedited RAW frame, NO skin smoothing, NO waxy CGI look, clean frame` |
| `3d` | `premium stylized 3D animation` | `premium stylized 3D animation, accurate proportions` | `premium stylized 3D animation` |
| `2d-animation` | `consistent 2D character design, defined linework, clean color fills, layout-friendly composition` | `consistent 2D object design, defined linework, clean color fills, layout-friendly composition` | combine both |
| `illustration` | `consistent illustration style, clean linework, monochrome or limited palette, editorial poster aesthetic` | (variants identical) | (variants identical) |

### §4.3 Shot subject classification (apply per shot in a storyboard)

For each shot, classify the main subject BEFORE composing the T2I:

- **Human subject** = the shot foregrounds a person, performer, or character (face / body / hands as the primary visual focus).
- **Product / object subject** = the shot foregrounds a product, prop, machine, food, environment, or any non-human object as the primary visual focus. Even shots that incidentally include human hands but center on the product belong here.
- **Mixed** = both human and product are co-equal in frame (e.g. a barista pouring coffee where both the hands AND the carafe are featured).

**Picking the wrong variant introduces noise.** Example: emitting `realistic human identity, unretouched skin texture with visible pores` on a shot of a coffee tower without humans pushes the T2I model to invent or merge human elements into the product frame — the machine and the cup get mashed together. This is why skin-texture tokens (pores, facial asymmetry, NO skin smoothing) live ONLY in the Human and Mixed columns, never in the Product/object column.

### §4.4 Domain-driven defaults

- When `domain = editorial-cinemagraph`, default mediaType is `illustration`.
- When `domain = product-demo`, default visualLock variant is **Product / object subject** (the product is the hero). Override per-shot to Human or Mixed if a shot specifically features a person.
- When `domain ∈ {narrative-character, real-interview, educational}`, default variant is **Human subject**. Override per-shot to Product/object for cutaway shots that focus on an object.
- When `domain = motion-explainer`, default mediaType is `2d-animation` (use `illustration` for a flatter editorial look), and the visualLock variant is the **Product / object** column — there is no human identity to preserve. Restate the palette and type system in every shot in place of a continuity anchor.

### §4.5 Photoreal close-up toolkit (`live` only, optional per shot)

Photographic realism comes from imperfection and concrete gear, not quality words. Apply only when a shot is an intimate facial close-up; skip for wider shots.

- Camera: name real gear, not quality words. Anti-pattern ❌ `8k, ultra realistic, extremely detailed face`. Correct ✅ `shot on a Canon EOS R5 with an 85mm f/1.4 prime lens wide open, focus locked on the near eye`.
- Lighting (fills the `<lighting>` slot, never visualLock): describe the source and its shadow, not the mood. Anti-pattern ❌ `cinematic dramatic lighting`. Correct ✅ `lit by a single large softbox high camera-left, soft falloff, the far side of the face dropping into shadow`.
- Framing: state distance and crop, not adjectives. Anti-pattern ❌ `beautiful close-up portrait`. Correct ✅ `extreme facial close-up, face fills the frame, top of head cropped above the hairline, eyes on the upper third`.

#### Acted live scenes in one room (field-tested 2026-10-24 on an acted pilot, VE photorealistic + ve-runner)

Two pilots of the same scene (narrated, then acted with lipsync dialogue, 19 shots). What held and what broke (`scripts/drama_sheet.py` enforces these when it writes the run sheet):

- **Paste the character line and the location line word for word into every shot** (official realistic-mini-dramas playbook). Before it, close-ups with no room reference drifted outdoors; after it, every close-up stayed in the room.
- **A set master (an empty-room image) in reference slot 2 is for wide shots only.** It locks the room (all wides matched) but also the camera: medium and close dialogue shots came back as full-room wides with the actor small. Give close-ups only the actor's master and let the verbatim location line carry the room; the cost is that furniture may sit on a different side.
- **Shots with no person are written as object photographs.** `someone's POV looking up at the ceiling` draws that someone; `architectural photograph, camera pointing straight up at the ceiling … only the ceiling, no person` works. Drop `shot on a cinema camera` from the style line for these shots and for master portraits: it drew a physical camera four times (ceiling, hospital corridor ×2, a master sheet).
- **A lipsync clip can end before its line does; check each one with ASR before assembly.** The clip length follows the generated speech rather than the slider (`04-platform-videoexpress.md`: an 8 s setting gave 4.5-6 s); in this pilot all nine dialogue clips came back 4.0 s from 5-6 s plans. Dead air before or after the line is not a problem: trim it in the edit. Only a line cut off at the clip's end needs action: re-roll the shot (adding `Right from the first second,` before the speaker's action fixed both truncated lines here, a sample of two), or keep the take and cut away to a reaction or listener shot while the full line plays from a separately voiced take.
- **An off-screen person named in a no-dialogue shot can walk in.** `a shadow of a person carrying a bucket passes across the paper window` became a man with a bucket entering the room. Keep such a person off the prompt (§11 closed cast) and let sound carry them.

#### Fast-cut montage and camera moves (field-tested 2026-11-04, 26 clips in 7 rounds, VE photorealistic + ve-runner, `--auto-pick`, one take each)

Test sheets and clips are in the author's own test project (not in this repository). Written as one plain English paragraph per I2V (not the eight tags), T2I = the opening frame. One take per idea, so these are leads, not rates.

- **One prompt can hold a whole montage.** Split the duration into timed segments (`0-2s: … 2-4s: cut to low angle, …`), add `fast cuts, transitions, speed ramps`, and VE cuts inside the clip in order: nail commercial (6 segments, about 8 shots), dance (5 of 5 segments), fight, tango, hip-hop. Use it for commercials, openings, dance and action; not for dialogue.
- **For action, short cut segments beat one continuous move.** `one slow pirouette` (8 s) gave a small leg lift; `one punch, one deflect` (6 s) was done in the first second, then 5 s of standing. The same scenes as 2 s cut segments were full and readable. A one-take shot works when it chains two or three moves (`two fast spins, then a long leap, then she sweeps down into a kneel … constant motion from the first frame to the last`).
- **Repeat the location in every segment.** With the bamboo courtyard named only in the opening, the last cut of the fight drifted to palm trees; with `in the bamboo courtyard` in every segment, it held. Same rule as the acted-scenes bullet above.
- **What you lock will not change.** `identical red nails in every moment` kept the nails green through four colour worlds even though each segment asked for a new colour (the dresses, not locked, changed). Lock only the face and hair; state the changing item per segment (`and now her nails are glossy cobalt blue`).
- **A transformation (A becomes B) needs its own short clip.** Match-cuts inside one 10 s clip (drop → nail, nail → pearl → peony) were skipped; a 5 s clip doing only `the drop falls and spreads into the nail` worked. Join the pieces in the edit.
- **Asking for words on screen gives garbled text.** `SILENT POWER typography` came back as `PLAYWEAR` / `SUSE`. Ask for clean negative space and add type in the edit (§10). Settings that usually carry signs (car parks) may still draw a level number.
- **Limbs: name the physics.** A solo dancer's feet twisted together; `she lands softly on one foot … feet, ankles and knees always bend the natural way and her legs never twist around each other` fixed it. For couples: `each dancer always has exactly two legs, and their legs stay clearly separate`. A tango dip came back with her hips and chest facing opposite ways; `her back arches backward in one smooth natural curve, her hips and chest facing the same direction as his, her head following her spine` fixed her, though his head then tilted back too.
- **Faces in fast cuts blur; say so.** `her face stays sharp, well lit and in focus in every shot, with no motion blur on her face` gave clear faces in the 16:9 retake.
- **VE does not orbit the camera; it turns the subject.** `bullet time … camera orbits 180 degrees`, `frozen like a 3D photograph, only the camera moves` and `360-degree orbit` all came back as the subject rotating in place with the background still (time never froze). Write with that: `extreme slow motion filmed at 1000 frames per second, camera locked … he very slowly rotates in mid-air … in the last second normal speed snaps back` reads as bullet time; a standing model rotating reads as a clean full-body turntable. Re-tested 2026-11-05 with three web "bullet time" prompts that name what is frozen and how the camera moves (`time is completely frozen … never move or fall. Only the camera moves: it smoothly orbits …`): a coffee-cup explosion kept splashing and settled, a jumping woman landed and walked off with the camera tracking sideways; spelling out the frozen subject does not help. **Product showcase that works:** T2I `premium product photograph … a futuristic sleek white and silver sneaker hovering in the centre of a dark studio, surrounded by frozen floating neon cyan and magenta particles and a splash of water frozen in mid-air … dramatic rim light`; I2V `Premium product showcase … Only the camera moves: it smoothly glides in a continuous loop around the sneaker to reveal its texture and design from all angles, the sneaker staying in the centre of the frame`. VE turns the product on its own axis with the light sweeping across it, which reads as a clean product turntable.
- **For flight and dives, shoot from inside the vehicle.** Cockpit POV (`從直升機駕駛艙內部透過前方擋風玻璃向下俯瞰…儀表板與駕駛艙框架在前景下方清晰可見`, then `機頭向下壓…俯衝進入峽谷…貼著溪流高速穿行`) gave a strong dive with the dashboard as a fixed foreground. Outside chase cams drifted: an FPV dive became a top-down glide, and a chase cam behind a diving eagle became the eagle flying away, though the end beat (talons take a fish) landed.
- **Bullet-dodge (Matrix-style) is unsolved.** `bends far backward … one hand reaching back toward the ground` drew a forward crouch in the T2I frame, so the whole clip was wrong; bullets written into the sky came out as tiny dots. What came out was still usable: the crouch with a slow push-in to the face (strong pose and camera) and a static sunglasses close-up; they did not like the bullet-macro passing the ear or the real-time dodge, which had been rated best from contact sheets. Judge action by playback, not contact sheets. Next attempt needs a different prompt; untried idea: `torso tilted back 45 degrees, chest facing the sky`, no hand on the ground.
- **9:16 vs 16:9 (same prompts).** 16:9 frames people smaller and full-body, more cinematic, with clearer faces; 9:16 makes motion and dives hit harder (the cockpit dive was weaker in 16:9, more of a level canyon run).
- **Tested 2026-11-05 (prompts from the web and our notes):**
  - **`Hard cut` between timed slices does not beat our plain timed slices** (v10a, the combat template's A/B labels and `Hard cut`): no visible difference from v7. Not worth adding.
  - **Decimal timing moves when an action happens, not how fast it is** (v10b, `0.5 seconds - A throws …`): the punch came at about that second at normal speed; the two fighters also swapped roles once. Use timestamps for order, not speed.
  - **A storyboard grid as the start image gives a push-in on the grid, not a film** (v14 parfait, a 10-panel ad board): the whole board zooms in, the panels never play. Saying `never show the grid … play the panels in reading order` (v14b) shows the grid first, then cuts to a few full-screen shots. **What works (v14c): the board as a Consistent Character reference (`Cast: Actor 1`) and a T2I of panel 1 only** (`Full-screen cinematic photo taken from the first panel … one single image with no grid`): person, red top, café and parfaits match the board; one take cut through several panels (pour, eat, lift the glass), the other stayed one continuous take, so VE reads the board's content but does not reliably cut per panel. VE T2I cannot draw a storyboard grid itself (v11: `create a 10 seconds storyboard image` gave a garbled poster).
  - **"Breaks out of the magazine" is unsolved** (v12–v12c, 9:16): writing the breakout shattered the woman herself (v12); `the printed page stays flat and whole … she comes alive … leans forward out of the page` kept her whole but nothing tore (v12b); a poster on a studio wall with the camera pulling back had her walk out while the photo strips scattered, not a punch-through, and burned the cover word in as garbled text (v12c). Next idea, untried: two shots, the paper tearing first (close-up, no person), then her stepping through the hole.
  - **A fast-cut travel vlog holds one person when the person is described in full in every slice** (v13 → v13b, Japan vlog, 1.6 s slices on a 125 bpm beat): with `a young Japanese-style woman` she changed between cuts; spelling out `a slim Japanese woman of about 23 with a round face, big dark eyes, straight black shoulder-length hair with soft bangs` in the T2I and the I2V kept her across outfit and place changes (same lesson as the nail ad). A Consistent Character reference on top (v13c) looked about the same: the description is enough.

---

## §5 first-last

ONE before/after frame pair plus one transition. Maps to VideoExpress's **"First Frame, Last Frame" (Beta)** card. Validated end-to-end 2026-08-09 (陶盆嫩芽 → 盛開萬壽菊, photorealistic, 9:16, 8s): frame consistency was excellent and the video generated cleanly.

Best for object transformations, state changes, before/after reveals, and time-lapse-feeling beats. Weakest for dialogue — prefer no speech here.

### §5.1 First-Last Hard Constraints

- Output exactly ONE frame pair (First Frame + Last Frame Smart Edit) plus ONE transition prompt. No storyboard, no extra shots.
- **The First Frame Prompt carries the COMPLETE scene description**: subject, environment, lighting, camera.
- **The Last Frame is a SMART EDIT of the first frame**, not a second full T2I: describe ONLY what changes, then explicitly pin everything else (e.g. `The pot, desk, window light, and background stay exactly the same.`). Never rewrite the full scene in the last-frame field — the platform edits the generated first image, and restating unchanged elements invites drift.
- The transition prompt describes one continuous motion arc that starts exactly at the First Frame state and ends exactly at the Last Frame state. Introduce nothing that appears in neither frame.
- **One state change per generation.** If the brief implies multiple transformations, pick the strongest single before/after and note the rest as follow-up pairs.
- Transition duration must fit the user-selected duration; one first-to-last generation caps at ~10 seconds (recommended 5-15s total content).
- If dialogue: ONE short line ≤ 100 characters, wrapped as a speech act per `01-core.md §3`. Otherwise prefer no dialogue — these read cleanest as pure visual transformations.
- Apply universal avoidances per `01-core.md §5`.

### §5.2 First-Last Output Format

Emit EXACTLY these three blocks, no intro text.

`### First Frame Prompt`
`<t2iBase> of <subject + setting> in the STARTING state: <state-specific details>, <camera + framing>, <lighting>, <visualLock>, wide <aspectRatio> composition, clean unmarked frame.`

`### Last Frame Smart Edit`
One short paragraph describing ONLY the change, then pinning the rest:
`The <subject> has <ending-state change>. The <list every unchanged element: subject identity / environment / lighting / background> stay exactly the same.`

`### Transition Prompt`
`Animate from the first frame to the last frame: <motion arc in 2-3 time-segmented beats, e.g. [0-2 seconds]: ..., [2-5 seconds]: ...>. Camera stays <locked / one slow move>. Keep subject identity, environment, palette, and lighting consistent throughout.` Plus, if dialogue, the speech-act wrap with a line ≤ 100 characters.

### §5.3 Platform facts for the user (2026-08-09 dogfood)

Mention these when the user is about to run the pair — they are the difference between a clean run and a wasted generation:

- Three fields in the modal: First Frame prompt · Last Frame Smart Edit · Video and Audio Prompt. Three buttons: Create First Image → Create Last Image → Create Video.
- Reference Photo Type select offers human / 2d / 3d / photorealistic / other.
- The duration slider lives behind Advanced Mode and **defaults to 7 seconds** here (range 3-10; the main generator defaults to 5).
- The platform's own red-text hint recommends **9:16 vertical** for this card.
- Image generation takes ~15-25 seconds per frame; the video takes ~2-3 minutes.
- The enhance checkbox in this modal is a different one from the main generator's — leave it off once the frames look right, same reasoning as the bible-drift rule.
- The media tile's right-click menu has **Save Last Frame**: save the ending frame and use it as the next pair's first frame. That is the platform's native support for chaining transitions into a longer sequence.
- This modal has no public-gallery checkbox.

### §5.4 First-Last Silent Quality Checks

- ✓ Exactly one First Frame Prompt + one Last Frame Smart Edit + one transition prompt, nothing else
- ✓ Last Frame Smart Edit describes only the changed elements and explicitly pins the unchanged ones
- ✓ Transition starts at the First Frame state and ends at the Last Frame state; no new elements introduced
- ✓ Transition duration within the user-selected duration (and ≤ ~10s per generation)
- ✓ Output contains no meta-commentary

---

## §6 short-form (retired 2026-09-19)

Retired. A vertical short (抖音 / Reels / TikTok) is a `storyboard` at 9:16 with the visual hook placed in Shot 1, 15-45 seconds, `minimal` output. No separate schema.
