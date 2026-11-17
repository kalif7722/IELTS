# IELTS Winners — Original GIF + Andrew US voice

This pipeline narrates **your supplied, unmodified GIF** using Microsoft `en-US-AndrewNeural`. It does **not** generate replacement slides, add zooms, highlighting, captions, overlays, or transitions.

## Prepare the source
Upload exactly one original GIF to the repository's `inputs/` folder, e.g. `inputs/lesson.gif`. PNG or WebP still images are also accepted, but they have no existing animation to preserve.

The renderer **never** makes placeholder artwork. If no input is uploaded, the job fails with a clear message.

## Narration
Edit `examples/examiners-margin.json` with narration corresponding to your uploaded GIF. For existing GIF slides, keep the narration in the same order as the displayed content. The current example narration explains the previously supplied Examiner's Margin introductory image.

## Run
Go to **Actions → Render IELTS Andrew US Reel → Run workflow**, or push the input. Download the MP4 and Andrew MP3 from the `ielts-andrew-us-reel` artifact.

GIF frames and transitions are preserved. The duration of each original frame is scaled **proportionally** to make the full GIF last as long as the narration. This changes playback speed but not frame content, order or animation. No other edits are made. If exact original timing is required instead, narration must be written to fit the existing GIF duration.

The voice synthesis service is an unofficial Edge TTS endpoint and can occasionally fail. No substitute voice will be used.
