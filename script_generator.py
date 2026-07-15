from google import genai
import json
import os
from datetime import datetime

# ============================================================
#   JANLO YAAR — Module 2: Script Writer
#   Topic uthao → Hinglish script banao → save karo
# ============================================================

# 🔑 Apni Gemini API key yahan daalo

# ⚙️ Setup
client = genai.Client(api_key=GEMINI_API_KEY)


# 📁 Folders
TOPICS_FILE = "topics.json"
SCRIPTS_DIR = "scripts"
os.makedirs(SCRIPTS_DIR, exist_ok=True)


def load_next_topic():
    """topics.json se pehla pending topic uthao"""

    if not os.path.exists(TOPICS_FILE):
        print("❌ topics.json nahi mila! Pehle topic_generator.py run karo.")
        return None

    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        all_topics = json.load(f)

    pending = [t for t in all_topics if t["status"] == "pending"]

    if not pending:
        print("⚠️  Koi pending topic nahi hai! topic_generator.py se naye topics banao.")
        return None

    print(f"📌 Topic mila: #{pending[0]['id']} — {pending[0]['title']}")
    return pending[0]


def generate_script(topic):
    """Ek topic ke liye poora Hinglish video script banao"""

    prompt = f"""
You are a viral Hinglish (use more English than Hindi) YouTube Shorts script writer for "Jaanlo_Yaar".

Topic: {topic['title']}
Pillar: {topic['pillar']}
Hook: {topic['hook']}

CRITICAL RULES FOR VIRAL SHORTS:
1. NEVER start with questions like "Kya tum jaante ho" or "Kya tumne suna hai"
2. ALWAYS start with a shocking or curiosity-driven statement
3. First line must hook within 2 seconds (scroll stopper)
4. Use numbers when possible (adds credibility)
5. Each line should feel connected like a flowing STORY (not random facts)
6. Keep each line 5-7 words max
7. Every next line should increase curiosity (no drop allowed)
8. Delay the full reveal till the end (build suspense)

STORY FLOW RULE (VERY IMPORTANT):
- Write like someone telling a shocking story step-by-step
- Each line should naturally lead to next
- Add open loops (incomplete info → viewer wants next line)
- Avoid robotic factual tone

GOOD FLOW EXAMPLES:
✔ "Ek din sab normal tha"
✔ "phir achanak kuch ajeeb hua"
✔ "log samajh hi nahi paaye"
✔ "par asli shock abhi baaki tha"

AVOID:
❌ disconnected facts
❌ textbook explanations
❌ boring wording like "iska reason ye tha"

HOOK FORMULA (use one):
- Direct Shock: "400 log nachte nachte mar gaye!"
- Number Shock: "1518 mein 400 logon ki maut hui"
- Unbelievable: "Doctors ne bola aur nacho!"
- Cliffhanger: "Wajah aaj bhi mystery hai..."

VIDEO STRUCTURE (15–25 sec, text-only):
- Line 1: HOOK (max 6 words, strong)
- Line 2: HOOK deepen (add intrigue)
- Line 3–?: STORY build (connected flow, suspense)
- Second last: TWIST (big reveal)
- Last: Shoulld be like that so person watches in loop

STYLE TAGGING:
- HOOK → shocking
- FACT → story progression
- TWIST → biggest shock
- CTA → call to action

Format each line as JSON:
{{"time": 0, "text": "text here", "style": "HOOK"}}

Return ONLY valid JSON object:
{{
  "topic_id": {topic['id']},
  "title": "{topic['title']}",
  "pillar": "{topic['pillar']}",
  "duration": 28,
  "lines": [...],
  "hashtags": ["#Jaanlo_Yaar", "#DarkFacts", "#HindiFacts"],
  "thumbnail_text": "MAX 4 WORDS CAPS"
}}

FINAL CHECK BEFORE OUTPUT:
- Does it feel like a STORY? (if no → rewrite)
- Does curiosity increase every line? (if no → fix)
- Is reveal delayed till end? (must)
"""

    print("✍️  Script likh raha hoon...")
    print("=" * 50)

    try:
        response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=prompt
)
        raw = response.text.strip()

        # Clean markdown if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        script = json.loads(raw)
        return script

    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"Raw response:\n{raw}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def save_script(script, topic_id):
    """Script ko scripts/ folder mein save karo"""

    filename = f"{SCRIPTS_DIR}/topic_{topic_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    print(f"✅ Script saved: {filename}")
    return filename


def update_topic_status(topic_id, status="scripted"):
    """Topic ka status update karo"""

    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        all_topics = json.load(f)

    for topic in all_topics:
        if topic["id"] == topic_id:
            topic["status"] = status
            topic["scripted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break

    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_topics, f, ensure_ascii=False, indent=2)

    print(f"✅ Topic #{topic_id} status → '{status}'")


def display_script(script):
    """Script ko terminal mein sundar display karo"""

    style_emojis = {
        "HOOK":  "🎣",
        "FACT":  "📖",
        "TWIST": "😱",
        "CTA":   "🔔",
    }

    print(f"\n🎬 SCRIPT: {script['title']}")
    print(f"⏱️  Duration: {script['duration']} seconds")
    print(f"🖼️  Thumbnail: {script.get('thumbnail_text', '')}")
    print("=" * 55)
    print(f"{'TIME':>5}  {'STYLE':<8}  TEXT")
    print("-" * 55)

    for line in script["lines"]:
        emoji = style_emojis.get(line["style"], "📌")
        print(f"{line['time']:>4}s  {emoji} {line['style']:<6}  {line['text']}")

    print("=" * 55)
    print(f"🏷️  Hashtags: {' '.join(script['hashtags'])}")
    print(f"\n💡 Next step: python video_editor.py")


# ============================================================
#   MAIN
# ============================================================
if __name__ == "__main__":
    print("\n✍️  JANLO YAAR — Script Writer")
    print("================================\n")

    # Step 1: Load next pending topic
    topic = load_next_topic()
    if not topic:
        exit()

    # Step 2: Generate script using Gemini
    script = generate_script(topic)
    if not script:
        print("❌ Script generate nahi hua. Dobara try karo!")
        exit()

    # Step 3: Save script to file
    save_script(script, topic["id"])

    # Step 4: Update topic status
    update_topic_status(topic["id"], "scripted")

    # Step 5: Display script
    display_script(script)
