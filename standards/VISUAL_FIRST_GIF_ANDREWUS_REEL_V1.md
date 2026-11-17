# VISUAL_FIRST_GIF_ANDREWUS_REEL_V1

**Canonical reusable workflow / standard for IELTS Winners and PTE Winners.**
Use this exact variable name in future chats: `VISUAL_FIRST_GIF_ANDREWUS_REEL_V1`.

## Objective

Convert a user-supplied **original animated GIF, preferably wrapped in a ZIP for transport**, into a narrated Instagram Reel with Microsoft Andrew US Neural voice. Deliver a verified MP4, ideally from GitHub Actions in `kalif7722/IELTS`. Preserve the original teaching artwork and existing transitions while synchronizing speech to the visual sequence.

## Non-negotiable rules

1. **Use only the actual user-supplied source** for this job. Never reuse a previous video, unrelated course image, cached narration, placeholder, reconstruction or generated picture.
2. Inspect the source ZIP/GIF **before** writing narration. Verify ZIP integrity, member GIF, actual frame count, dimensions, frame order, original durations and source hashes. A .gif filename may contain static PNG data; verify actual file type and frame count.
3. **Visual-first script:** Write narration independently for EACH original frame based on exactly what that frame depicts. Explain its title, instructional content, diagrams, highlighted words, and examples in the correct order. Do not invent figures, statements or off-screen concepts. If a slide has a visible factual error, preserve artwork and avoid repeating it as fact; note it in review.
4. Voice must be **`en-US-AndrewNeural`**, via Edge TTS or compatible Microsoft neural TTS. Default rate `-4%`. Do not silently use another voice. Retry short-lived `NoAudioReceived` failures, but report persistent failure.
5. **No newly created visual effects:** no zoom, panning, animated highlights, subtitles, captions, extra transitions, cropping, rearrangement, watermarks or re-created slides. Use the source frames as-is, in their existing order.
6. Synthesize a separate MP3 for each frame. Measure each actual MP3 duration using ffprobe. Extend or retime ONLY the associated original frame to fit narration, plus a small natural pause (roughly 0.4–0.5 s). Never apply a single blind global speed multiplier or narrate a different frame.
7. Reel maximum **less than 180 seconds**. Aim around 100–155 seconds for comfortable teaching. Use concise but pedagogically complete narration; shorten if needed without dropping essential visible points. Reject outputs above the cap rather than trimming mid-sentence.
8. **Quality preservation:** Original GIF frame resolution (e.g. 864×1536) or equivalent exact aspect ratio; do not use WhatsApp-compressed MP4 intermediates. H.264 MP4 with CRF ~17–18, yuv420p, 24–30 fps, AAC 192 kbps, faststart. Do not claim upscaling improves source text.
9. **QA is mandatory:** Inspect source frames, verify the narration-to-frame order, inspect exported video frame boundaries and manifest, verify audio exists, correct voice was requested, resulting resolution, duration and MP4 integrity. A successful GitHub job alone does NOT prove content alignment.
10. Prefer **ZIP containing the original GIF** uploaded directly to the repository `inputs/`. If not possible from ChatGPT, ask user to upload; do not claim GitHub file upload succeeded. Avoid producing a purported final download link until the file is verified to exist.

## Reuse pattern for the next new file

- Read and reference this standard by name.
- Inspect the new uploaded ZIP (not another file from a previous chat), identify frame order and content, and extract any original GIF without changing its pixels.
- Write a fresh **per-slide** config JSON with exact source filename, ZIP/GIF SHA-256, frame count, dimensions, slide titles, narrated text, and duration cap.
- Prefer reusing renderer `render_ielts_gif_original.py` or `render_pte_gif_original.py`; generalize cautiously to new titles/slide counts. Do not hardcode previous source hashes or scene text for the new job.
- Add a uniquely scoped GitHub Actions workflow trigger for that specific source path, not a broad `inputs/**` trigger, to avoid launching unrelated workflows.
- Render and examine the run logs, the timing/scene manifest, and the MP4. Link the **correct** run artifact. Never substitute an artifact from a similarly named previous workflow.
- When the upload contains a genuine animated within-slide sequence, preserve its internal ordered frames/transitions and adjust the relevant durations rather than flattening the visual content.

## Existing implementation references

- Repo: https://github.com/kalif7722/IELTS
- IELTS five-frame GIF code: `render_ielts_gif_original.py`
- IELTS config: `examples/ielts-table-original-gif.json`
- IELTS action: `.github/workflows/render-ielts-table-original-gif.yml`
- PTE seven-frame GIF code: `render_pte_gif_original.py`
- PTE config: `examples/pte-original-gif.json`
- PTE action: `.github/workflows/render-pte-original-gif.yml`
- Earlier lower-resolution MP4 renderers are historical and are **not** the default standard.

## New-chat invocation

> Follow `VISUAL_FIRST_GIF_ANDREWUS_REEL_V1` from `kalif7722/IELTS/standards/VISUAL_FIRST_GIF_ANDREWUS_REEL_V1.md`. Inspect my newly uploaded ZIP/GIF first, prepare slide-by-slide Andrew US narration matching the actual frames, preserve all original visuals/transitions, render through GitHub Actions under three minutes, and verify the output artifact.

**Status:** This document defines the approved process; it is not an assertion that every past rendered video was fully quality-checked.
