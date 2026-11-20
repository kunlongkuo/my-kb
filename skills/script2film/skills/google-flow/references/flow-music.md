# Google Flow Music: songs and instrumentals

Site: `https://www.flowmusic.app/`. Google AI Pro includes its Plus plan (shown as PLUS under the account name), with its own credits, separate from Flow video. Checked 2026-11-20; the interface there was mostly English with Chinese headings.

## Steps

1. **Sign in.** 「使用 Google 帳戶繼續」 (continue with Google) is the user's step. First use only: a welcome and terms flow.
2. **Compose.** Open a session (「New session」 or the one in use), then the Compose panel (the pen icon at the top right; `find` "Compose"). It has:
   - **Lyrics**: section tags in square brackets work (`[Verse 1]`, `[Pre-Chorus]`, `[Chorus]`, `[Bridge]`, `[Instrumental]`, `[Outro]`). Turn on **Instrumental** for music without singing.
   - **Sound**: the style description (below).
   - **Details**: title and other options.
   Paste with `find` → click the box → `type` (line breaks are kept). The panel starts empty in a new session.
3. **Generate.** About half a minute to a minute for a full song; it appears in the session as a track (the first full song was 2:56, the second 3:01). The session's chat box ("Ask Producer") is an assistant that rewrites; Compose sends exactly what you wrote.
4. **Listen before downloading** or let the user listen: the first take of a style may miss.
5. **Download.** The track's 「⋯」 → Download → WAV, MP3 or M4A, or Get stems. In the test the WAV item did not start a download from an automated click while MP3 did from the user's own click; if nothing lands in `~/Downloads` within a minute, ask the user to click it, and check that Chrome is not blocking automatic downloads for the site.
6. **Ingest.** `python3 skills/google-flow/scripts/flow_ingest.py --latest music --to <project>/flow_bgm.wav --model "Flow Music" --prompt-file <sound-and-lyrics.txt> --doc <project>/doc.json` sets `bgm.src` and `bgm.credit` and keeps the other `bgm` keys (`gain_db` stays as set; the series rule is the bed at -36 dB under narration).

## Writing the Sound line

What worked on 2026-11-20 with the same Mandarin lullaby lyrics:

- Genre and feel first, then tempo, then the voice, then the instruments by section, then the ending, then what to leave out. A second take, aiming at a gentler jazz-pop style:

  > Soft acoustic jazz-pop lullaby with a gentle bossa nova lilt, late-night coffeehouse intimacy, about 72 BPM, laid-back and unhurried. Warm, sweet, intimate female vocal sung softly and close to the microphone, effortless and conversational, slightly breathy, gentle Mandarin phrasing with lots of space between lines. Instruments: mellow felt piano with simple jazzy chords, warm nylon-string guitar playing a light bossa nova pattern, soft upright bass, brushed snare and very light shaker, a touch of Rhodes in the chorus. Melodic, singable, memorable chorus melody. Never dramatic or belting; the final chorus just gets a little fuller and warmer. Ends quietly on solo piano and a soft hum. No choir, no backing vocals, no big drums.

- **Describe a singer's style, do not name the singer.** When asked for "like <singer>", write the traits instead (intimate piano-and-voice jazz, Brazilian-style bossa nova): it avoids artist-name filters and imitating a real voice.
- A "smoky jazz, 66 BPM, muted trumpet" description gave good sound quality but a melody that missed: ask for a "melodic, singable, memorable chorus" explicitly.
- Keep section-by-section arrangement notes in the Sound line, not in the lyric tags; tags like `[Intro | 4 bars piano]` are read as lyrics on some takes.

## Lyrics and rights

The lyrics must be the user's own (or public domain). Scripture verses in a song: use the translation the project uses and check its licence. Google does not claim ownership of what Flow Music makes; whether Flow Music grants commercial use (YouTube monetisation, distribution) is not stated plainly on the pages found on 2026-11-20, so label the published film as AI-generated (`--synthetic`) and have the user check the current terms before selling or distributing a song.
