"""Use the uploaded original GIF/PNG unchanged; add only Andrew US voice.

For GIFs, frames and their ordering are preserved. Frame display durations are
scaled uniformly when necessary to fit the narration. No new graphics, crops,
zoom, overlays, or transitions are introduced.
"""
import asyncio
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist"
VOICE = "en-US-AndrewNeural"
FPS = 30

def execute(args):
    subprocess.run(args, check=True)

def duration(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True).strip())

def select_input():
    folder = ROOT / "inputs"
    supplied = sorted(p for p in folder.glob("*") if p.suffix.lower() in (".gif", ".png", ".webp"))
    if not supplied:
        raise FileNotFoundError(
            "No original image/GIF found. Upload the unmodified file to inputs/. "
            "A recreated placeholder is never used."
        )
    if len(supplied) != 1:
        raise ValueError("Keep exactly one .gif, .png, or .webp file in inputs/ for this run.")
    return supplied[0]

def narration_text():
    cfg = json.loads((ROOT / "examples" / "examiners-margin.json").read_text())
    if "narration" in cfg:
        return cfg["narration"]
    # Existing per-scene script is also supported, but without visual edits.
    return " ".join(x["narration"] for x in cfg["scenes"])

async def synthesize(script, filename):
    import edge_tts
    await edge_tts.Communicate(script, VOICE, rate="-5%").save(str(filename))

def make_video(source, soundtrack, target):
    with tempfile.TemporaryDirectory(prefix="ielts-frames-") as tmp:
        tmp = Path(tmp)
        with Image.open(source) as im:
            animated = getattr(im, "n_frames", 1) > 1
            frames = []
            durations = []
            for i, frame in enumerate(ImageSequence.Iterator(im)):
                rgba = frame.convert("RGBA")
                # Preserve every pixel and original frame size. The codec is yuv420p,
                # so slight compression is unavoidable, but no content changes.
                composed = Image.new("RGBA", rgba.size, "white")
                composed.alpha_composite(rgba)
                filename = tmp / f"frame-{i:05d}.png"
                composed.convert("RGB").save(filename)
                frames.append(filename)
                durations.append(max(20, int(frame.info.get("duration", im.info.get("duration", 100)))))
        if not frames:
            raise ValueError("Input image has no frames.")
        # GIF displays have no soundtrack. Fit the entire existing animation once
        # to the audio length while preserving relative frame timings.
        audio_length = duration(soundtrack)
        target_length = audio_length + 0.6
        source_seconds = sum(durations) / 1000
        scale = target_length / source_seconds
        manifest = tmp / "frames.txt"
        with manifest.open("w") as fp:
            for name, ms in zip(frames, durations):
                fp.write(f"file '{name.as_posix()}'\\n")
                fp.write(f"duration {ms / 1000 * scale:.6f}\\n")
            # concat demuxer requires repeating the final frame for its duration
            fp.write(f"file '{frames[-1].as_posix()}'\\n")
        execute([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-safe", "0", "-f", "concat", "-i", str(manifest),
            "-i", str(soundtrack), "-filter:v",
            "fps=30,format=yuv420p", "-af", "apad",
            "-t", str(target_length), "-c:v", "libx264", "-crf", "18",
            "-preset", "veryfast", "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart", str(target)
        ])
        return {
            "source": str(source.relative_to(ROOT)),
            "frame_count": len(frames),
            "animated_input": animated,
            "original_animation_seconds": source_seconds,
            "narrated_seconds": duration(target),
            "duration_scale": scale,
            "voice": VOICE,
            "alterations": "None; frame timing scaled uniformly to fit narration",
        }

async def main():
    OUT.mkdir(exist_ok=True)
    source = select_input()
    audio = OUT / "andrew-us.mp3"
    await synthesize(narration_text(), audio)
    if not audio.exists() or audio.stat().st_size < 1000:
        raise RuntimeError("Andrew US audio generation failed. No substitute voice used.")
    movie = OUT / "IELTS-Original-GIF-Andrew-US.mp4"
    info = make_video(source, audio, movie)
    (OUT / "render-manifest.json").write_text(json.dumps(info, indent=2))
    print("SUCCESS:", movie, json.dumps(info))

if __name__ == "__main__":
    asyncio.run(main())
