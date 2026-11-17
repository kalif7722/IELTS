# IELTS Winners — Andrew US visual-first reel renderer

This GitHub Actions workflow produces a narrated **1080 × 1920 MP4** with Microsoft **en-US-AndrewNeural** voice (via Edge TTS), plus individual audio segments.

## Use the original artwork
Upload your current slide to **`inputs/examiners-margin.png`** in this repository. Until this image exists, the renderer deliberately outputs a **preview recreation**, not your original picture. Uploaded GIFs require frame extraction and scene timing support in a subsequent iteration; the current input is a PNG.

## Rendering
Push `inputs/examiners-margin.png`, or navigate to **Actions → Render IELTS Andrew US Reel → Run workflow**. The video should appear in **Artifacts → ielts-andrew-us-reel** once the run succeeds.

The narration segments and highlighted portions of the visual are stored in [examples/examiners-margin.json](examples/examiners-margin.json). Each segment's screen duration is automatically measured from its Andrew-generated MP3, so visuals and speech stay aligned.

Edge TTS is an unofficial public endpoint; synthesis can sometimes fail due to service connectivity. The workflow fails instead of substituting an unwanted voice.
