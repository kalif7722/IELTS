"""IELTS Winners — Andrew US Neural, scene-by-scene visual-first reel rendering."""
import asyncio, json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"dist"
VOICE="en-US-AndrewNeural"
def command(cmd):
    subprocess.run(cmd,check=True)
def probe(path):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],text=True).strip())
def compose(source,focus,index):
    # Original slide remains fully visible throughout, with a soft focus outline.
    with Image.open(source) as loaded:
        im=Image.new("RGB",(1080,1920),"#fffdf6")
        picture=ImageOps.contain(loaded.convert("RGB"),(1050,1850),Image.Resampling.LANCZOS)
        ox=(1080-picture.width)//2; oy=(1920-picture.height)//2
        im.paste(picture,(ox,oy))
        y1=int(oy+focus[0]*picture.height)
        y2=int(oy+focus[1]*picture.height)
        d=ImageDraw.Draw(im,"RGBA")
        if index:
            d.rounded_rectangle((max(12,ox-6),max(12,y1-10),min(1068,ox+picture.width+6),min(1908,y2+10)),radius=18,outline=(226,110,29,230),width=8)
        dest=OUT/f"scene-{index:02d}.png";im.save(dest)
        return dest
def demo(path):
    # The demo is intentionally distinct from the user's original image.
    im=Image.new("RGB",(750,1334),"#fffdf5");d=ImageDraw.Draw(im)
    f="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    def title(t,y,sz=28):d.text((375,y),t,font=ImageFont.truetype(f,sz),anchor="ma",fill="#19315b")
    title("IELTS WINNERS",110,36);title("Examiner's Margin",230,42)
    title("Household Expenditure",310,29)
    for i,t in enumerate(["Canada   Japan   Mexico   Germany","Housing   28%   24%   20%   26%","Food        16%   18%   24%   17%","Transport   12%   10%   14%   12%","Others      14%   48%   42%   45%"]):
        title(t,400+i*68,23)
    title("A four-paragraph Task 1 report",840,29)
    for i,t in enumerate(["Identify comparisons","Select key figures","Structure a report","Use useful vocabulary"]):title(t,945+i*75,27)
    path.parent.mkdir(parents=True,exist_ok=True);im.save(path)
async def speech(text,path):
    import edge_tts
    await edge_tts.Communicate(text,VOICE,rate="-5%").save(str(path))
async def run():
    OUT.mkdir(exist_ok=True)
    data=json.loads((ROOT/"examples/examiners-margin.json").read_text())
    original=ROOT/"inputs/examiners-margin.png"
    if original.exists():
        source=original
    else:
        source=ROOT/"inputs/demo-preview.png";demo(source)
        print("WARNING: Original PNG not found. Rendering preview artwork. Upload inputs/examiners-margin.png for final version.")
    segments=[]
    for i,scene in enumerate(data["scenes"]):
        audio=OUT/f"voice-{i:02d}.mp3"
        await speech(scene["narration"],audio)
        if not audio.exists() or audio.stat().st_size < 1000:
            raise RuntimeError(f"Andrew US narration missing for scene {i}")
        dur=probe(audio)+float(scene.get("pause",0.45))
        visual=compose(source,scene["focus"],i)
        output=OUT/f"segment-{i:02d}.mp4"
        frames=math.ceil(dur*24)
        # Every segment is paced by the actual synthesized spoken duration.
        command(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","24","-i",str(visual),"-i",str(audio),"-vf","zoompan=z='min(zoom+0.00007,1.035)':d=1:s=1080x1920:fps=24,format=yuv420p","-frames:v",str(frames),"-af","apad","-t",str(frames/24),"-c:v","libx264","-preset","veryfast","-crf","24","-r","24","-c:a","aac","-b:a","160k","-ar","44100","-ac","2",str(output)])
        segments.append(output)
    manifest=OUT/"concat.txt"
    manifest.write_text("".join("file '"+str(p.resolve()).replace("'","")+"'\n" for p in segments))
    final=OUT/"IELTS-Examiners-Margin-Andrew-US.mp4"
    command(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(manifest),"-c","copy","-movflags","+faststart",str(final)])
    (OUT/"render-manifest.json").write_text(json.dumps({"voice":VOICE,"original_slide":source==original,"scenes":len(segments),"seconds":probe(final),"output":final.name},indent=2))
    print("SUCCESS",final,"seconds",probe(final),"original artwork used:",source==original)
if __name__=="__main__":asyncio.run(run())
