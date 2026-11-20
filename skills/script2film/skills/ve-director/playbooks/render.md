# Step 3 — Render the approved plan

Read `references/render-rules.md` and `references/styles/<mediaType>.md` (and `references/dialogue.md` if there are spoken lines). Do not re-plan.

## Rules

- **The approved plan outranks the rulebook** on anything it decides: shot count, seconds, framing, left/right placement, who is in frame and whether their face is visible, action steps, camera, prop detail, sound. In particular, consecutive shots may share a camera move (e.g. several `locked off`) and sizes may repeat — the rulebook's rotation defaults apply only to plans made without a handbook.
- Language: the §0.1 繁中 template is the shape; the English per-shot template in §1.2a shows structure only. The style's `t2iBase` opener is translated into Chinese like everything else (§0 keeps only the tags, `Actor N`, `16:9` and lens tokens in English).
- Multi-Actor shots: the Scene Lock sentence repeats verbatim (§1.2a Multi-character) — that outranks the general "do not repeat setting sentences" craft note; all other setting and lighting wording varies.
- **開始狀態 is the first frame; 結束狀態 is the last [ACTION] segment's end.** The T2I draws exactly the plan's 開始狀態 (pose, side of the boundary, place in frame), and `[IDENTITY / CONTINUITY]` states the same starting positions; the last `[ACTION]` lands on the 結束狀態 and holds it. Bound every motion with a distance or an end pose (「前進約 60 公分」「停在畫面中央偏左」) rather than an adverb.
- Everything the plan does not decide follows `render-rules.md`: the eight-tag I2V grammar, the §0 language rule, locks, burned-in-text hygiene, scale lock, the style's `[LIGHT AND IMAGE]` and `[NEGATIVES]`.
- **Mouth locks (`render-rules.md` §11), copied verbatim:** a plan cell `Actor N（臉不可見）` → the sentence `Actor N 的臉全程不可見。` and no lock; a non-human face (角色: 是否人類臉 = 否) → the fangs variant; an action that covers the mouth with a hand → the hand variant; the speaker of a quoted line in this shot → no lock (their mouth must move); every other visible face, listeners included → the standard closed-lips lock.
- One portrait per Actor in the plan's 角色 block. Prompt bodies use `Actor N` only; the plan's 原文動作 column is review-only and never copied. Spoken lines stay exactly as the plan quotes them, names included.
- A row whose 景別 contains `｜硬切｜` renders with the hard-cut variant (`render-rules.md` § FROM 07-experimental.md §2); say in the delivery line that it is an experimental shot.
- Output exactly the minimal format of `render-rules.md` §1.2a, timestamps `00:00-00:06`. Emit every shot in one answer.

Save as `storyboard.md` (see SKILL.md § Files).

## Check

Run, from the skill directory:

```
python3 scripts/lint.py <storyboard.md> --min <lower bound s> --max <upper bound s> --names "<every 名字 from the plan's 角色 block that is not —, comma-separated, e.g. 趙雲,糜夫人,阿斗; never role nouns such as 美女 or 惡鬼>" --human "<Actor N list with 是否人類臉 = 是>"
```

- Exit 0 → report `檢查通過：N 顆、X 秒` and deliver.
- Exit 1 → for each failing shot, re-render that shot alone from its plan row, replace it in the file, run lint again. Never search-and-replace across the file. If the same failure survives a re-render unchanged, stop re-rendering: the rule or the checker may be wrong. Report the lint line, quote the rule you followed, and ask — never add text you believe is wrong just to pass the check.
- No shell available → run the same checks by reading: timestamps `00:00` and continuous, total in range, eight tags in order, no character names, a mouth sentence for every visible human face, `無文字` in every T2I.

## Deliver

Tell the user in 2-3 lines: shot count and runtime, the check result, and the one shot most likely to need a re-roll in VideoExpress and why (a soft-material manipulation, a crowded frame, a transformation cut).

Then give the one command that runs the saved storyboard with ve-runner (`storyboard.md` is already its run-sheet format; it reads the Actor portraits as character masters and infers each shot's cast from the `Actor N` it names):

```
python3 <repo>/tools/ve-runner/ve_runner.py <absolute path to storyboard.md> [flags]
```

`<repo>` is the PromptStudio repo: two levels above the resolved skill directory (`skills/ve-director` → `../..`); print it as an absolute path.

Flags come only from what the loaded style file states, never from guesswork: its field notes say Creative mode on → `--creative`; an Image Type other than Photorealistic → `--image-type <type>`; "two or three takes per shot" → `--takes 3`. A style file with no generator settings gets no flags except Creative mode, decided by how much the look asks of the generator: simple flat drawings (stick figures, plain line art, flat icons) leave it off, where Creative only adds ways to go wrong; detailed or varied looks (stop-motion, puppets, painted, 3D, photoreal sets) get `--creative`. This is a working rule from production runs, not an A/B result; a style's own field notes override it. When the storyboard sits in a film's folder (for example `<projects>/<film>/`), add `--run-dir <that folder>/ve-runs` so the run's records stay with the film. Add one line on QC: candidates are picked at each gate, interactively or with `python3 <repo>/tools/ve-runner/ve_qc.py <run dir> [choice]`, where `<run dir>` is the path the runner prints on its first line.
