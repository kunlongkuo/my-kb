# Step 5 — Revise

Classify every follow-up turn first:

| The user… | Do |
|---|---|
| asks a question about the plan or a shot | answer only; do not re-emit anything |
| reports a VideoExpress result (「第 3 顆臉跑掉」「出現字幕」) | diagnose first: is it the first frame (T2I), the motion (I2V), or a platform limit? Name the cause, propose the smallest fix, and ask before changing |
| changes the story, order, number of shots, or who is in a shot | this is a plan change: update the affected plan rows, show only those rows, wait (CP1 again) |
| changes wording, a prop, a sound, a camera move inside one shot | re-render only that shot from its (updated) plan row |

When emitting a revision, output only the changed shots under a first line `修訂：shot N`, and state 「其餘 shot 不變」. Never restart from shot 1. Run the check (render.md § Check) on the full file after replacing the changed shots.

The rulebook outranks the conversation: if a requested change breaks a hard rule (a name in a prompt body, a morph inside one shot, a third person in a two-person cap), say so in one line and offer the closest compliant version.
