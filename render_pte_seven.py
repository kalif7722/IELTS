"""Original PTE seven-slide MP4 + Andrew US speech, no visual effects."""
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "examples/pte-read-aloud-seven-scenes.json"

def invoke(*command):
    subprocess.run(command, check=True)

def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(path)
    ], text=True))

async def voice(text, path, name):
    import edge_tts
    for attempt in range(1, 6):
        try:
            path.unlink(missing_ok=True)
            await edge_tts.Communicate(text, name, rate="-4%").save(str(path))
            if path.is_file() and path.stat().st_size > 1000:
                return
            raise RuntimeError("No audio data returned")
        except Exception as error:
            if attempt == 5:
                raise RuntimeError("Andrew US audio failed after five attempts") from error
            print(f"Voice retry {attempt}: {error}", flush=True)
            await asyncio.sleep(attempt * 6)

async def main():
    cfg = json.loads(CONFIG.read_text())
    source = ROOT / cfg["source"]
    if not source.is_file():
        raise FileNotFoundError(f"Upload original video to {cfg['source']} (no replacement media allowed)")
    movie_stream = next(s for s in probe(source)["streams"] if s["codec_type"] == "video")
    size = (int(movie_stream["width"]), int(movie_stream["height"]))
    if size != (360, 640):
        raise RuntimeError(f"Unexpected source size {size}; expected the original 360x640")
    with tempfile.TemporaryDirectory(prefix="pte-seven-") as folder:
        tmp = Path(folder)
        invoke("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-i", str(source), "-vsync", "0", str(tmp / "source-%03d.png"))
        frames = sorted(tmp.glob("source-*.png"))
        scenes = cfg["scenes"]
        expected_titles = (
            "Introduction", "Step 1", "Step 2", "Step 3",
            "Step 4", "Step 5", "Five scientific sentences",
        )
        actual_titles = tuple(scene["title"] for scene in scenes)
        if any(not title.startswith(label) for title, label in zip(actual_titles, expected_titles)):
            raise RuntimeError(
                "PTE narration order does not match approved original frame order: "
                + repr(actual_titles)
            )
        if len(frames) != len(scenes):
            raise RuntimeError(f"Expected {len(scenes)} source slides; found {len(frames)}")
        print(f"Validated {len(frames)} original source frames in unchanged sequence", flush=True)
        scene_files, log = [], []
        for index, (frame, scene) in enumerate(zip(frames, scenes), 1):
            sound = tmp / f"voice-{index:02}.mp3"
            await voice(scene["narration"], sound, cfg["voice"])
            seconds = float(probe(sound)["format"]["duration"]) + 0.4
            clip = tmp / f"clip-{index:02}.mp4"
            invoke("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                   "-loop", "1", "-framerate", "24", "-i", str(frame),
                   "-i", str(sound), "-t", f"{seconds:.3f}",
                   "-vf", "format=yuv420p", "-c:v", "libx264",
                   "-crf", "17", "-preset", "medium", "-r", "24",
                   "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                   "-ac", "2", "-af", "apad", str(clip))
            scene_files.append(clip)
            log.append({"slide":index,"title":scene["title"],"duration":round(seconds,2)})
            print(f"Slide {index}/{len(frames)}: {seconds:.2f}s — {scene['title']}", flush=True)
            if sum(s["duration"] for s in log) >= cfg["max_seconds"]:
                raise RuntimeError("Narration exceeds the strict under-three-minute limit")
        list_file = tmp / "concat.txt"
        list_file.write_text("".join(f"file '{p.resolve()}'\n" for p in scene_files))
        target = ROOT / cfg["output"]
        target.parent.mkdir(parents=True,exist_ok=True)
        invoke("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-f", "concat", "-safe", "0", "-i", str(list_file),
               "-c", "copy", "-movflags", "+faststart", str(target))
        total = float(probe(target)["format"]["duration"])
        if not 0 < total < 180:
            target.unlink(missing_ok=True)
            raise RuntimeError(f"Invalid final duration {total:.2f}s")
        result = {"source":cfg["source"],"voice":cfg["voice"],
                  "duration_seconds":round(total,2),
                  "resolution":f"{size[0]}x{size[1]}",
                  "original_frame_count":len(frames),
                  "visual_changes":"None — original video frames and order retained",
                  "additional_transitions":False,"scenes":log}
        (target.parent / "pte-seven-render-manifest.json").write_text(json.dumps(result,indent=2))
        print("RENDER SUCCESS:",target,"DURATION",total,flush=True)

if __name__ == "__main__":
    asyncio.run(main())
