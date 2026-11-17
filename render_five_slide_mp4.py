"""Narrate five original frames with Andrew US. No new visual effects."""
import argparse, asyncio, json, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def cmd(args): subprocess.run(args,check=True)
def info(path): return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(path)],text=True))
async def say(words,out):
    import edge_tts
    await edge_tts.Communicate(words,"en-US-AndrewNeural",rate="-4%").save(str(out))
    if not out.is_file() or out.stat().st_size < 1000: raise RuntimeError("Andrew US audio missing")
async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",default="inputs/IELTS-5-slide-original.mp4")
    ap.add_argument("--script",default="examples/ielts-five-slide-voice.json")
    ap.add_argument("--output",default="dist/IELTS-5-Slides-Andrew-US.mp4")
    ap.add_argument("--verify-only",action="store_true")
    args=ap.parse_args()
    src=ROOT/args.source
    if not src.is_file(): raise FileNotFoundError(f"Missing ORIGINAL MP4: {src}. Upload this exact source; no substitute.")
    scene_data=json.loads((ROOT/args.script).read_text())["scenes"]
    v=next(x for x in info(src)["streams"] if x["codec_type"]=="video")
    if (int(v["width"]),int(v["height"]))!=(360,640): raise ValueError("Unexpected source size, expected 360x640")
    with tempfile.TemporaryDirectory() as tmp:
        work=Path(tmp)
        cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(src),"-vsync","0",str(work/"frame-%03d.png")])
        frames=sorted(work.glob("frame-*.png"))
        if len(frames)!=len(scene_data): raise ValueError(f"Expected {len(scene_data)} original frames; found {len(frames)}")
        print(f"Verified {len(frames)} original slide frames.",flush=True)
        if args.verify_only:return
        parts=[]; report=[]
        for i,(frame,scene) in enumerate(zip(frames,scene_data),1):
            audio=work/f"andrew-{i:02d}.mp3"
            await say(scene["narration"],audio)
            length=float(info(audio)["format"]["duration"])+0.45
            part=work/f"scene-{i:02d}.mp4"
            cmd(["ffmpeg","-hide_banner","-loglevel","error","-y",
                "-loop","1","-framerate","24","-i",str(frame),"-i",str(audio),
                "-t",f"{length:.3f}","-vf","format=yuv420p",
                "-c:v","libx264","-preset","slow","-crf","17","-r","24",
                "-c:a","aac","-b:a","192k","-ar","44100","-ac","2","-af","apad",str(part)])
            parts.append(part)
            report.append({"slide":i,"title":scene["title"],"seconds":round(length,3)})
            print(f"Slide {i}: {scene['title']} ({length:.1f}s)",flush=True)
        if sum(x["seconds"] for x in report)>=179: raise RuntimeError("Narration too long for a 3-minute Reel")
        concat=work/"list.txt"
        concat.write_text("".join("file '"+str(p.resolve())+"'\n" for p in parts))
        dst=ROOT/args.output;dst.parent.mkdir(parents=True,exist_ok=True)
        cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy","-movflags","+faststart",str(dst)])
        actual=float(info(dst)["format"]["duration"])
        if actual>=180: raise RuntimeError(f"Final video {actual:.2f}s exceeds three minutes")
        result={"voice":"en-US-AndrewNeural","source":args.source,"output":args.output,"duration_seconds":actual,"resolution":"360x640","source_frames":len(frames),"added_effects":False,"scenes":report}
        (dst.parent/"render-manifest.json").write_text(json.dumps(result,indent=2))
        print("RENDER OK",json.dumps(result),flush=True)
if __name__=="__main__":asyncio.run(main())
