import json
import os
import requests
import random
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
from moviepy.video.fx.all import fadein, fadeout
from google import genai
from datetime import datetime

# ============================================================
#   JANLO YAAR — Module 3: Video Editor
#   Script uthao → background video + text + music = final video
# ============================================================

# 🔑 API Keys — Apni keys yahan daalo
PEXELS_API_KEY = "3EiAwD05lE6LJPhau5CgPzRvjDIQOTYnqGj6G3807pKCNtKAwERAthv4"
GEMINI_API_KEY = "AIzaSyDFGw5ZMlJgMgY3lx1zwGjn3F-Ss_kfbVE"
# ⚙️ Setup Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
 
# 📁 Folders
SCRIPTS_DIR = "scripts"
OUTPUT_DIR  = "output/videos"
META_DIR    = "output/metadata"
MUSIC_DIR   = "assets/music"
FONTS_DIR   = "assets/fonts"
TEMP_DIR    = "temp"
 
for d in [OUTPUT_DIR, META_DIR, MUSIC_DIR, FONTS_DIR, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)
 
# 📱 Shorts dimensions
WIDTH  = 1080
HEIGHT = 1920
 
# 🎵 Music map
MUSIC_MAP = {
    "Dark History" : "dark_suspense.mp3",
    "Science"      : "mind_blown.mp3",
    "Money & Power": "epic_dramatic.mp3",
    "Mystery"      : "creepy_ambient.mp3",
    "World Facts"  : "creepy_ambient.mp3",
}
 
# 🎨 Text colors per style
STYLE_COLORS = {
    "HOOK"  : "#FFD600",
    "FACT"  : "#FFFFFF",
    "TWIST" : "#FF3131",
    "CTA"   : "#FFD600",
}
 
# 🎨 Overlay darkness per style
STYLE_OVERLAY = {
    "HOOK"  : 0.65,
    "FACT"  : 0.55,
    "TWIST" : 0.70,
    "CTA"   : 0.60,
}
 
 
# ============================================================
#   STEP 1: Script Load
# ============================================================
def load_script(topic_id):
    path = f"{SCRIPTS_DIR}/topic_{topic_id}.json"
    if not os.path.exists(path):
        print(f"❌ Script nahi mila: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
 
 
# ============================================================
#   STEP 2: Gemini se Image Keywords Banao
# ============================================================
def generate_image_keywords(script):
    """Har line ke liye Gemini se perfect image search keyword banao"""
 
    lines_text = "\n".join(
        [f"Line {i+1} ({l['style']}): {l['text']}" for i, l in enumerate(script["lines"])]
    )
 
    prompt = f"""
You are helping create a viral Hinglish YouTube Shorts video for topic: "{script['title']}"
 
Here are the text lines that will appear on screen:
{lines_text}
 
For each line, suggest a short Pexels image search keyword (2-4 words in English) that best matches the visual feel of that line.
The images should be dramatic, dark, cinematic and engaging & real if possible.
 
Return ONLY a valid JSON array with exactly {len(script['lines'])} keywords:
["keyword1", "keyword2", "keyword3", ...]
 
Rules:
- Keywords must be in English
- 2-4 words max per keyword
- Match the mood: HOOK=mysterious, FACT=relevant visual, TWIST=dramatic/dark, CTA=fire/energy
- No repetition
"""
 
    try:
        response = client.models.generate_content(model="gemini-3-flash-preview",contents=prompt)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        keywords = json.loads(raw.strip())
        print(f"✅ {len(keywords)} image keywords ready!")
        return keywords
    except Exception as e:
        print(f"⚠️  Keyword generation failed: {e} — using defaults")
        pillar_defaults = {
            "Dark History" : "dark medieval history",
            "Science"      : "science laboratory dark",
            "Money & Power": "luxury money power",
            "Mystery"      : "mysterious dark fog",
            "World Facts"  : "earth aerial dramatic",
        }
        default = pillar_defaults.get(script["pillar"], "dark dramatic")
        return [default] * len(script["lines"])
 
 
# ============================================================
#   STEP 3: Pexels se Images Download Karo
# ============================================================
def download_image(keyword, index):
    """Pexels se ek image download karo"""
 
    headers = {"Authorization": PEXELS_API_KEY}
    params  = {
        "query"      : keyword,
        "per_page"   : 10,
        "orientation": "portrait",
    }
 
    try:
        r    = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
        data = r.json()
 
        if not data.get("photos"):
            print(f"  ⚠️  '{keyword}' — koi image nahi mili, black frame use karunga")
            return None
 
        photo    = random.choice(data["photos"][:5])
        img_url  = photo["src"]["large2x"]
        img_data = requests.get(img_url, timeout=15).content
 
        path = f"{TEMP_DIR}/bg_{index}.jpg"
        with open(path, "wb") as f:
            f.write(img_data)
 
        return path
 
    except Exception as e:
        print(f"  ⚠️  Image download failed for '{keyword}': {e}")
        return None
 
 
# ============================================================
#   STEP 4: Text Frame Banao (PIL)
# ============================================================
def create_frame(bg_path, text, style, width=WIDTH, height=HEIGHT):
    """Cinematic background + bold text frame"""

    import random

    # Background load
    if bg_path and os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGB")

        # smart crop (center focus)
        bg_w, bg_h = bg.size
        target_ratio = width / height
        current_ratio = bg_w / bg_h

        if current_ratio > target_ratio:
            new_w = int(bg_h * target_ratio)
            x1 = (bg_w - new_w) // 2
            bg = bg.crop((x1, 0, x1 + new_w, bg_h))
        else:
            new_h = int(bg_w / target_ratio)
            y1 = (bg_h - new_h) // 2
            bg = bg.crop((0, y1, bg_w, y1 + new_h))

        bg = bg.resize((width, height), Image.LANCZOS)
    else:
        bg = Image.new("RGB", (width, height), (10, 10, 10))

    # 🔥 Gradient overlay (top darker, bottom lighter)
    overlay = Image.new("RGBA", (width, height))
    for y in range(height):
        opacity = int(180 * (y / height))  # gradient
        for x in range(width):
            overlay.putpixel((x, y), (0, 0, 0, opacity))

    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)

    # 🎨 Style config
    color = STYLE_COLORS.get(style, "#FFFFFF")
    font_size = 110 if style == "HOOK" else 90

    font_paths = [
        f"{FONTS_DIR}/bold.ttf",
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except:
                continue

    if not font:
        font = ImageFont.load_default()

    # 🧠 Smart wrap (balanced lines)
    words = text.split()
    lines = []
    curr = ""

    for word in words:
        test = f"{curr} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)

        if bbox[2] > width - 150:
            lines.append(curr)
            curr = word
        else:
            curr = test

    if curr:
        lines.append(curr)

    # 🎯 Vertical center slightly up (better composition)
    line_h = font_size + 20
    total_h = len(lines) * line_h
    y = int((height - total_h) * 0.45)

    # ✨ Draw text with glow + stroke
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2

        # Glow
        for dx in range(-6, 7, 2):
            for dy in range(-6, 7, 2):
                draw.text((x + dx, y + dy), line, font=font, fill="#000000")

        # Main text
        draw.text((x, y), line, font=font, fill=color)

        y += line_h

    # 🔥 subtle watermark (clean)
    try:
        wm_font = ImageFont.truetype(font_paths[1], 32)
    except:
        wm_font = ImageFont.load_default()

    draw.text((width - 420, height - 100),
              "@Jaanlo_Yaar",
              font=wm_font,
              fill="#FFD60088")

    return bg.convert("RGB")
 
# ============================================================
#   STEP 5: Video Assemble
# ============================================================
def assemble_video(script, frame_paths, music_path=None):
    print("\n🎞️  Cinematic video assemble ho raha hai...")

    import random
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from moviepy.editor import ImageClip, CompositeVideoClip

    lines = script["lines"]
    duration = script["duration"]
    topic_id = script["topic_id"]

    clips = []

    # =========================================================
    # 🔥 INTRO (NO IMAGEMAGICK — PURE PIL)
    # =========================================================
    img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 120)
    except:
        font = ImageFont.load_default()

    text = "WAIT..."
    bbox = draw.textbbox((0, 0), text, font=font)

    x = (WIDTH - (bbox[2] - bbox[0])) // 2
    y = (HEIGHT - (bbox[3] - bbox[1])) // 2

    draw.text((x, y), text, font=font, fill="white")

    intro = ImageClip(np.array(img)).set_duration(0.6)
    clips.append(intro)

    # =========================================================
    # 🎬 MAIN CLIPS
    # =========================================================
    for i, line in enumerate(lines):
        start = line["time"] + 0.6
        end = lines[i + 1]["time"] + 0.6 if i + 1 < len(lines) else duration + 0.6
        dur = end - start

        base = ImageClip(frame_paths[i]).set_duration(dur)

        # 🎯 SLIGHT SHAKE
        def shake(get_frame, t):
            dx = random.randint(-2, 2)
            dy = random.randint(-2, 2)
            return get_frame(t)

        base = base.fl(shake)

        clip = (
            base
            .set_start(start)
            .crossfadein(0.25)
        )

        clips.append(clip)

    # =========================================================
    # 🎞️ FINAL VIDEO (NO AUDIO)
    # =========================================================
    final = CompositeVideoClip(clips, size=(WIDTH, HEIGHT)).set_duration(duration + 0.6)

    # =========================================================
    # 💾 EXPORT
    # =========================================================
    out_path = f"{OUTPUT_DIR}/topic_{topic_id}.mp4"

    print(f"💾 Exporting → {out_path}")
    print("⏳ Rendering cinematic video...")

    final.write_videofile(
        out_path,
        fps=30,
        codec="libx264",
        audio=False,  # 🔥 important
        logger=None,
    )

    return out_path
# ============================================================
#   STEP 6: Metadata Generate + Save
# ============================================================
def generate_metadata(script):
    print("\n📝 Metadata generate ho raha hai...")
 
    prompt = f"""
You are a YouTube SEO expert for a Hinglish dark facts channel "JanloYaar".
 
Video topic: {script['title']}
Pillar: {script['pillar']}
 
Generate optimized upload metadata in JSON:
{{
  "youtube_title": "Catchy Hinglish title max 70 chars with 1-2 emojis and imporatn hashtags for viral videos",
  "youtube_description": "Hinglish description with hook + what video covers + CTA. End with:\\n\\n🔔 Subscribe: @Jaanlo_Yaar\\n📸 Instagram: @jaanlo.yaar\\n\\n",
  "youtube_tags": ["tag1", "tag2" ... upto 500 char limit],
  "instagram_caption": "3 punchy Hinglish lines + emojis + hashtags(5).",
  "hashtags": ["#JanloYaar", "#HindiFacts" ... ]
}}
 
Return ONLY valid JSON.
"""
 
    try:
        response = client.models.generate_content(model="gemini-3-flash-preview",contents=prompt)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"⚠️  Metadata failed: {e} — using basic metadata")
        return {
            "youtube_title"      : script["title"],
            "youtube_description": f"{script['title']}\n\n🔔 Subscribe: @JanloYaar\n📸 Instagram: @janlo.yaar",
            "youtube_tags"       : ["JanloYaar", "HindiFacts", "DarkFacts", "Shorts"],
            "instagram_caption"  : f"{script['title']} 🤯\n\n#JanloYaar #HindiFacts",
            "hashtags"           : ["#JanloYaar", "#HindiFacts", "#Shorts"],
        }
 
 
def save_metadata(metadata, topic_id):
    # JSON save
    json_path = f"{META_DIR}/topic_{topic_id}_metadata.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
 
    # Human readable TXT save
    txt_path = f"{META_DIR}/topic_{topic_id}_upload_info.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("  JANLO YAAR — UPLOAD INFO\n")
        f.write("=" * 60 + "\n\n")
        f.write("📌 YOUTUBE TITLE:\n")
        f.write(metadata["youtube_title"] + "\n\n")
        f.write("📝 YOUTUBE DESCRIPTION:\n")
        f.write(metadata["youtube_description"] + "\n\n")
        f.write("🏷️  YOUTUBE TAGS:\n")
        f.write(", ".join(metadata["youtube_tags"]) + "\n\n")
        f.write("📸 INSTAGRAM CAPTION:\n")
        f.write(metadata["instagram_caption"] + "\n\n")
        f.write("🔖 ALL HASHTAGS:\n")
        f.write(" ".join(metadata["hashtags"]) + "\n")
 
    print(f"✅ Upload info saved: {txt_path}")
    return txt_path
 
 
def display_metadata(metadata):
    print("\n" + "=" * 60)
    print("📋 UPLOAD METADATA READY — Copy paste karo!")
    print("=" * 60)
    print(f"\n📌 YouTube Title:\n   {metadata['youtube_title']}")
    print(f"\n📝 Description (first 2 lines):")
    for line in metadata["youtube_description"].split("\n")[:2]:
        print(f"   {line}")
    print(f"\n🏷️  Tags: {', '.join(metadata['youtube_tags'][:6])}...")
    print(f"\n📸 Instagram: {metadata['instagram_caption'][:80]}...")
    print(f"\n🔖 Hashtags: {' '.join(metadata['hashtags'][:5])}...")
    print("=" * 60)
 
 
# ============================================================
#   CLEANUP
# ============================================================
def cleanup_temp():
    import shutil
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)
    print("🧹 Temp files clean!")
 
 
# ============================================================
#   MAIN
# ============================================================
if __name__ == "__main__":
    print("\n🎬 JANLO YAAR — Video Editor (Upgraded)")
    print("=========================================\n")
 
    # Load scripted topic
    scripted_id = None
    if os.path.exists("topics.json"):
        with open("topics.json", "r", encoding="utf-8") as f:
            topics = json.load(f)
        scripted = [t for t in topics if t["status"] == "scripted"]
        if scripted:
            scripted_id = scripted[0]["id"]
 
    if not scripted_id:
        print("❌ Koi scripted topic nahi! Pehle script_writer.py run karo.")
        exit()
 
    script = load_script(scripted_id)
    if not script:
        exit()
 
    print(f"📌 Topic  : #{scripted_id} — {script['title']}")
    print(f"🎭 Pillar : {script['pillar']}")
    print(f"⏱️  Duration: {script['duration']}s | Lines: {len(script['lines'])}\n")
 
    # Step 1: Image keywords
    print("🤖 Har line ke liye image keywords bana raha hoon...")
    keywords = generate_image_keywords(script)
 
    # Step 2: Download + create frames
    print(f"\n⬇️  {len(keywords)} images download ho rahi hain Pexels se...")
    frame_paths = []
 
    for i, (line, keyword) in enumerate(zip(script["lines"], keywords)):
        print(f"  [{i+1}/{len(keywords)}] '{keyword}' → {line['text'][:35]}...")
        bg_path    = download_image(keyword, i)
        frame_img  = create_frame(bg_path, line["text"], line["style"])
        frame_path = f"{TEMP_DIR}/frame_{i}.jpg"
        frame_img.save(frame_path, quality=95)
        frame_paths.append(frame_path)
 
    print(f"\n✅ Saari {len(frame_paths)} frames ready!")
 
    # Step 3: Music
    music_file = MUSIC_MAP.get(script["pillar"], "dark_suspense.mp3")
    music_path = f"{MUSIC_DIR}/{music_file}"
    if not os.path.exists(music_path):
        print(f"⚠️  Music nahi mili: {music_path} — bina music ke chalega")
        music_path = None
 
    # Step 4: Assemble video
    video_path = assemble_video(script, frame_paths, music_path)
 
    # Step 5: Cleanup temp
    cleanup_temp()
 
    # Step 6: Generate + save metadata
    metadata     = generate_metadata(script)
    metadata_txt = save_metadata(metadata, scripted_id)
    display_metadata(metadata)
 
    # Step 7: Update topic status
    with open("topics.json", "r", encoding="utf-8") as f:
        all_topics = json.load(f)
    for t in all_topics:
        if t["id"] == scripted_id:
            t["status"]    = "filmed"
            t["filmed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break
    with open("topics.json", "w", encoding="utf-8") as f:
        json.dump(all_topics, f, ensure_ascii=False, indent=2)
 
    print(f"\n🎉 SAB KUCH READY HAI YAAR!")
    print(f"🎬 Video       : {video_path}")
    print(f"📋 Upload Info : {metadata_txt}")
    print(f"💡 Next Step   : python thumbnail_maker.py")
