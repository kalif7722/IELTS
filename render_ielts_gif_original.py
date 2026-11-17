"""Render the exact five-frame IELTS GIF from its original ZIP with Andrew US.

No generated images, overlays, zooms, crops or additional transitions.
The only visual change is the duration each original GIF frame is displayed.
"""
import asyncio
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path
from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "examples/ielts-table-original-gif.json"
OUT = ROOT / "dist"

def execute(command):
    subprocess.run(command, check=True)

def length(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True).strip())

def validate_source(cfg, work):
    original_zip = ROOT / cfg["source"]
    if not original_zip.is_file():
        raise FileNotFoundError(
            f"Upload your unchanged high-quality ZIP to {cfg['source']} first."
        )
    packed = original_zip.read_bytes()
    if hashlib.sha256(packed).hexdigest() != cfg["zip_sha256"]:
        raise RuntimeError("ZIP SHA-256 mismatch. This is not the verified source file.")
    with zipfile.ZipFile(original_zip) as archive:
        files = [name for name in archive.namelist()
                 if not name.endswith("/") and name.lower().endswith(".gif")]
        if len(files) != 1:
            raise RuntimeError("ZIP must contain exactly one original animated GIF.")
        gif_bytes = archive.read(files[0])
    if hashlib.sha256(gif_bytes).hexdigest() != cfg["gif_sha256"]:
        raise RuntimeError("Original GIF SHA-256 mismatch.")
    gif_path = work / "original.gif"
    gif_path.write_bytes(gif_bytes)
    frames = []
    with Image.open(gif_path) as animation:
        if animation.n_frames != cfg["expected_frame_count"]:
            raise RuntimeError(
                f"Expected {cfg['expected_frame_count']} frames; found {animation.n_frames}"
            )
        if list(animation.size) != cfg["expected_resolution"]:
            raise RuntimeError(f"Unexpected original resolution: {animation.size}")
        for index, frame in enumerate(ImageSequence.Iterator(animation), 1):
            # A simple full-frame conversion preserves source artwork.
            dest = work / f"original-{index:02d}.png"
            frame.convert("RGBA").save(dest)
            frames.append(dest)
    return frames

async def generate_voice(script, target, voice):
    import edge_tts
    for attempt in range(1, 6):
        try:
            target.unlink(missing_ok=True)
            await edge_tts.Communicate(script, voice, rate="-4%").save(str(target))
            if target.is_file() and target.stat().st_size > 1000:
                return
            raise RuntimeError("No audio returned")
        except Exception as exc:
            if attempt == 5:
                raise RuntimeError("Andrew US narration unavailable after retries") from exc
            print(f"Voice retry {attempt}: {exc}", flush=True)
            await asyncio.sleep(6 * attempt)

async def main():
    cfg = json.loads(CONFIG.read_text())
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ielts-gif-original-") as folder:
        work = Path(folder)
        frames = validate_source(cfg, work)
        scenes = cfg["scenes"]
        if len(frames) != len(scenes):
            raise RuntimeError("Number of narration segments must match original GIF frames.")
        print("Verified original 864x1536 GIF, 5 frames, source checksums match.",flush=True)
        segments, timeline = [], []
        for index, (frame, scene) in enumerate(zip(frames, scenes), 1):
            mp3 = work / f"andrew-{index:02}.mp3"
            await generate_voice(scene["narration"], mp3, cfg["voice"])
            seconds = length(mp3) + 0.45
            output = work / f"part-{index:02}.mp4"
            # Static original GIF frame; only on-screen time changes.
            execute([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-loop", "1", "-framerate", "24", "-i", str(frame),
                "-i", str(mp3), "-t", f"{seconds:.3f}",
                "-vf", "format=yuv420p", "-c:v", "libx264",
                "-preset", "medium", "-crf", "17", "-r", "24",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                "-ac", "2", "-af", "apad", str(output)
            ])
            segments.append(output)
            timeline.append({
                "frame": index, "title": scene["title"],
                "duration_seconds": round(seconds, 2)
            })
            print(f"Frame {index}/5: {seconds:.2f}s, {scene['title']}",flush=True)
            if sum(item["duration_seconds"] for item in timeline) >= cfg["maximum_duration"]:
                raise RuntimeError("Speech exceeds strict Instagram 3-minute limit.")
        playlist = work / "concat.txt"
        playlist.write_text("".join(f"file '{p.resolve()}'\n" for p in segments))
        final = OUT / "IELTS-Table-Original-GIF-Andrew-US.mp4"
        execute([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(playlist),
            "-c", "copy", "-movflags", "+faststart", str(final)
        ])
        video_duration = length(final)
        if video_duration >= 180 or video_duration <= 0:
            final.unlink(missing_ok=True)
            raise RuntimeError(f"Rendered video duration invalid: {video_duration}")
        report = {
            "original_zip": cfg["source"], "original_sha256": cfg["zip_sha256"],
            "voice": cfg["voice"], "resolution": "864x1536",
            "frame_count": len(frames),
            "output": final.name, "video_duration_seconds": round(video_duration, 3),
            "visual_changes": "None. Original GIF frames and order preserved; timing adjusted.",
            "additional_effects": False, "scenes": timeline
        }
        (OUT / "ielts-table-gif-manifest.json").write_text(json.dumps(report,indent=2))
        print("RENDER SUCCESS", json.dumps(report),flush=True)

if __name__ == "__main__":
    asyncio.run(main())
