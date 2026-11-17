"""Narrate an EXISTING MP4 with Andrew US and retime its original slide intervals.

All source frames, slide order and original transitions are retained.
No synthetic graphics, zooms, captions or extra effects are generated.
"""
import asyncio
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist"
CONFIG = ROOT / "examples" / "ielts-table-mp4.json"

def run(args):
    subprocess.run(args, check=True)

def probe(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True).strip())

async def generate_audio(script, voice, target):
    import edge_tts
    await edge_tts.Communicate(script, voice, rate="-5%").save(str(target))
    if not target.is_file() or target.stat().st_size < 1000:
        raise RuntimeError("Andrew US speech synthesis returned no audio")

async def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    source = ROOT / cfg["input"]
    if not source.is_file():
        raise FileNotFoundError(
            f"Source MP4 missing at {source}. Upload the original unchanged MP4 "
            "to inputs/IELTS_Task1_Table_Narrated_Reel.mp4"
        )
    if source.suffix.lower() != ".mp4":
        raise ValueError("This workflow only accepts the original MP4")
    OUT.mkdir(exist_ok=True)
    source_length = probe(source)
    if abs(source_length - cfg["source_duration"]) > 0.7:
        raise ValueError(
            f"Wrong input video: got {source_length:.2f} s, expected "
            f"{cfg['source_duration']:.2f} s"
        )
    scene_files, info = [], []
    for index, scene in enumerate(cfg["scenes"], 1):
        a, b = float(scene["start"]), float(scene["end"])
        original_length = b - a
        if original_length <= 0:
            raise ValueError(f"Bad time interval for scene {index}")
        audio = OUT / f"andrew-scene-{index:02d}.mp3"
        print(f"Scene {index}: {scene['title']}", flush=True)
        await generate_audio(scene["narration"], cfg["voice"], audio)
        spoken = probe(audio)
        target_length = spoken + 0.35
        ratio = target_length / original_length
        part = OUT / f"scene-{index:02d}.mp4"
        # Precise source trim; change only playback speed of the ORIGINAL footage.
        # Existing transitions remain within their original intervals.
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(source), "-i", str(audio),
            "-filter_complex",
            (
                f"[0:v]trim=start={a:.3f}:end={b:.3f},"
                f"setpts=(PTS-STARTPTS)*{ratio:.9f},"
                f"fps=24,format=yuv420p[v];"
                "[1:a]apad=pad_dur=0.35[a]"
            ),
            "-map", "[v]", "-map", "[a]",
            "-t", f"{target_length:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
            "-video_track_timescale", "90000",
            str(part)
        ])
        scene_files.append(part)
        info.append({
            "slide": index, "title": scene["title"], "original_start": a,
            "original_end": b, "source_seconds": original_length,
            "voice_seconds": spoken, "final_seconds": probe(part),
            "speed_multiplier": round(original_length / target_length, 4)
        })
    concat = OUT / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in scene_files))
    final = OUT / "IELTS-Table-Andrew-US-Synced.mp4"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c", "copy", "-movflags", "+faststart", str(final)
    ])
    summary = {
        "source": str(source.relative_to(ROOT)),
        "voice": cfg["voice"],
        "source_seconds": source_length,
        "output_seconds": probe(final),
        "output": final.name,
        "scene_count": len(scene_files),
        "visual_changes": "None. Original source MP4 trimmed and time-adjusted per slide.",
        "scenes": info
    }
    (OUT / "render-manifest.json").write_text(json.dumps(summary, indent=2))
    print("COMPLETE", final, "duration", summary["output_seconds"], flush=True)

if __name__ == "__main__":
    asyncio.run(main())
