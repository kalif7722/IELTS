"""Narrated IELTS reel using Microsoft Andrew US Neural."""
import argparse, asyncio, json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
ROOT=Path(__file__).parent.resolve()

def demo(path):
    """Generate a clearly labeled placeholder, NOT the original user artwork."""
    im=Image.new("RGB",(1080,1920),"#fffdf6")
    d=ImageDraw.Draw(im)
    f="/usr/share/fonts/truetype/dejavu/DejaVuSans"
    def ft(n,b=False): return ImageFont.truetype(f+("/DejaVuSans-Bold.ttf" if b else "/DejaVuSans.ttf"),n)
    def center(t,y,n=38,col="#17254a",b=False):
        d.text((540,y),t,fill=col,font=ft(n,b),anchor="ma")
    d.rounded_rectangle((80,80,1000,184),24,fill="#173c78")
    center("IELTS Academic Writing Task 1",152,43,"white",True)
    center("IELTS WINNERS",235,38,"#173c78",True)
    d.rounded_rectangle((135,280,945,400),24,fill="#fbea86")
    center("Examiner's Margin",364,62,"#242339",True)
    center("Household Expenditure",455,43,"#382751",True)
    x=[50,320,490,660,840,1030]; y=540;dy=86
    rows=[["Category","Canada","Japan","Mexico","Germany"],["Housing","28%","24%","20%","26%"],["Food","16%","18%","24%","17%"],["Transport","12%","10%","14%","12%"],["Others","14%","48%","42%","45%"]]
    for a in x: d.line((a,y,a,y+5*dy),fill="#507083",width=4)
    for j in range(6):d.line((x[0],y+j*dy,x[-1],y+j*dy),fill="#507083",width=4)
    for j,row in enumerate(rows):
        for i,s in enumerate(row):
            d.text(((x[i]+x[i+1])//2,y+j*dy+dy//2),s,font=ft(26 if i else 29,True),fill="#172438",anchor="mm")
    center("How to analyse and compare",1075,46,"#2b2443",True)
    center("data in a 4-paragraph",1145,45,"#2b2443",True)
    center("Task 1 response",1215,45,"#2b2443",True)
    d.rounded_rectangle((90,1310,990,1765),25,outline="#527578",width=4)
    center("In this lesson, you will learn:",1380,38,"#182e3a",True)
    for j,s in enumerate(["Identify key comparisons","Select important figures","Structure a four-paragraph report","Use effective vocabulary","Write a strong overview"]):
        d.text((136,1445+j*63),"✓  "+s,font=ft(30),fill="#246a55")
    center("Let's break it down step by step!",1840,35,"#262947",True)
    path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path)

async def speak(script,mp3,voice):
    import edge_tts
    await edge_tts.Communicate(script,voice,rate="-5%").save(str(mp3))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--voice",default="en-US-AndrewNeural")
    args=p.parse_args()
    source=ROOT/"inputs/examiners-margin.png"
    if not source.exists():
        source=ROOT/"inputs/demo-preview.png";demo(source)
        print("WARNING: Original slide missing. Using preview recreation instead.")
    out=ROOT/"dist";out.mkdir(exist_ok=True)
    words=json.loads((ROOT/"examples/examiners-margin.json").read_text())["slides"][0]["narration"]
    audio=out/"andrew-us.mp3"
    asyncio.run(speak(words,audio,args.voice))
    if not audio.exists() or audio.stat().st_size<1000:raise RuntimeError("TTS audio was not generated")
    raw=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(audio)],text=True)
    duration=float(raw.strip())+.8
    with Image.open(source) as im:
        background=Image.new("RGB",(1080,1920),"white")
        fitted=ImageOps.contain(im.convert("RGB"),(1080,1920),Image.Resampling.LANCZOS)
        background.paste(fitted,((1080-fitted.width)//2,(1920-fitted.height)//2))
        background.save(out/"frame.png")
    output=out/"ielts-examiners-margin-andrew-us.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-loop","1","-framerate","24","-i",str(out/"frame.png"),"-i",str(audio),"-af","apad","-t",str(duration),"-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p","-r","24","-c:a","aac","-b:a","160k","-movflags","+faststart",str(output)],check=True)
    (out/"manifest.json").write_text(json.dumps({"voice":args.voice,"source":str(source.relative_to(ROOT)),"original_image_used":source.name=="examiners-margin.png","duration_seconds":duration},indent=2))
    print("Rendered:",output)
if __name__=="__main__":main()
