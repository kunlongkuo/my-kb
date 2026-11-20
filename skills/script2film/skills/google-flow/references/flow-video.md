# Google Flow: video (Omni, Veo)

Site: `https://flow.google.com/`. Needs Google AI Plus, Pro or Ultra. Checked 2026-11-20 on Google AI Pro with the interface in Traditional Chinese; labels below are the zh-TW ones with the English meaning. The interface changes often: when a step does not match, take a screenshot and find the control by its role (`find` / `read_page`), not by position.

## What it costs

The settings chip in the prompt box shows the price before you send (「生成內容會使用 N 點」, "this uses N credits"). Measured on Omni 1.2 Flash: 360p, 10 s, ×2 = 20 credits. Google AI Pro gives 1,000 credits a month (shared with Whisk) plus a small daily allowance; check the current numbers on the user's account, not in blogs. A job refused by policy is refunded.

## Steps

1. **Project.** Home → 「新增專案」 (new project), or open the user's existing one. First use only: a welcome dialog (leave the marketing and research boxes unticked), the privacy policy page, and feature tours; these are the user's to accept unless they have said you may handle such dialogs.
2. **Manual mode.** The prompt box has a spark switch (Flow Agent). Turn it off: the agent rewrites the prompt and asks its own questions. With it off, the chip next to the send button shows the model.
3. **Settings chip.** Click it:
   - 「影片」 (video), then 「素材」 (ingredients: reference images keep faces and places) or 「影格」 (frames: first / last frame).
   - 16:9 or 9:16.
   - Model: Omni 1.2 Flash is the default and the one tested. Omni 1.1 Flash and Veo 3.1 Fast / Quality showed 「即將於 12月5日停用」 (retiring 5 Dec) on 2026-11-20.
   - 360p or 720p, length (slider, 3–15 s on Omni 1.2), outputs ×1–×4.
   - Read the credit line and **tell the user the number before sending** (see SKILL.md).
4. **Reference image.** 「+」 in the prompt box opens the media picker. Images already uploaded to the project are listed; a new one goes in through 「上傳媒體」 (upload media). That button opens the system file dialog, which the browser tools cannot drive: capture the file input instead (snippet below), then `file_upload` to its ref. Upload only images the user made or may use; Flow asks to confirm the rights on the first upload (「這張圖像的使用權」, "rights to this image"). Pick the image, then 「新增至提示詞」 (add to prompt): its thumbnail sits at the top of the prompt box.
5. **Prompt.** Type it (writing rules below), then the arrow to send. Each output is a tile with a percentage; about one to two minutes for 10 s at 360p.
6. **Download.** Open the tile → download icon (「下載媒體」) → 270p GIF, 360p original, or **720p upscaled (「已提升畫質」)**. Upscaling takes a few seconds to a minute, then the file lands in `~/Downloads`. A 360p clip offered 720p, not 1080p. Download one at a time and wait for each file; after the first one Chrome may block further automatic downloads from the site (an icon at the right of the address bar). Allowing them is a browser setting: ask the user.
7. **Ingest.** `python3 skills/google-flow/scripts/flow_ingest.py --latest video --to <project>/ve_<look>/shotK.mp4 --model "Omni 1.2 Flash" --settings "360p, 10 s, 9:16, downloaded 720p" --prompt-file <prompt.txt>`. Look at `shotK.sheet.jpg` before using the clip.

Capture the upload input. Run this in the page with the media picker open; it clicks 「上傳媒體」 itself and keeps the file input on the page instead of opening the dialog. Then `find` "file input" for its ref:

```js
const oc = HTMLInputElement.prototype.click;
HTMLInputElement.prototype.click = function () {
  if (this.type === 'file') { this.style.display = 'block'; if (!this.isConnected) document.body.appendChild(this); return; }
  return oc.call(this);
};
[...document.querySelectorAll('button')].find(b => b.textContent.includes('上傳媒體'))?.click();
```

## Failures

| Tile says | Cause seen | Do |
|---|---|---|
| 「這個生成內容可能違反我們的政策」 (may violate policy) | blood, injuries in a fight | rewrite without them (a sparring match, the loser rolls and gets up); refunded |
| 「無法生成音訊」 (could not generate audio) | gunfire in the sound line | rewrite the sound line (no weapons); Flow also offers to return silent video in its settings |

Do not retry the same prompt; change what triggered it.

## Writing the prompt (Omni 1.2 Flash)

Plain English sentences; the model knows the world, so describe intent, not every detail. Measured on 2026-11-20:

- **Name the reference.** "The young man in the white uniform from the reference image (same face, …)". Faces and clothes held in every test.
- **Motion that flows: one continuous action plus one camera path.** Three fight versions with the same reference:
  - time blocks ("0–4 s … 4–7 s …") → each block played as a separate pose: looked like a demonstration;
  - hard cuts every 2 s, a new angle each → more angles, still move-by-move;
  - "one single continuous take", every block flowing into a counter, a handheld camera that rushes in, whips around, ducks low, tracks backward → the most fluid, motion blur on hands and feet.
  Watched in full, all three still read as two people running a routine rather than a wide-swinging fight scene. Big martial-arts action is a weak spot; do not promise it.
- **Bullet time works**: one moment, extreme slow motion, the subject bending back while projectiles pass with air-distortion trails, then a snap back to full speed. The camera turned only part of the way round although the prompt asked for 360°.
- **Selfie vlog works** (9:16): a character reference, "smartphone front-camera selfie look", walking a named street at a named time of day, the line to say in quotes with the accent ("in a natural Taiwanese Mandarin accent: \"…\""), "Exactly one person talking to camera", and "No music. No subtitles, no on-screen text."
- **Sound** is generated with the picture: write a "Sound:" line (ambience, footsteps, impacts, the voice). It cannot take an audio file.
- End with "No text, no subtitles." Omni draws captions otherwise.

## Where this fits

The clips go where `docs/FLOW.md` Optional A "Using another platform for the shots" says: `<project>/ve_<look>/shotK.mp4`, then `ve_clipcheck.py <project>/ve_<look> --strips`. VideoExpress stays the default for series work; Flow is for a shot VE could not make, a vertical vlog line, or when VE is down.
