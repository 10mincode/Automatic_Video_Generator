from google import genai
import json
import os
from datetime import datetime

# ============================================================
#   JANLO YAAR — Module 1: Topic Generator
#   Har week 7 trending dark/mystery fact topics generate karo
# ============================================================

# 🔑 Apni Gemini API key yahan daalo

# ⚙️ Setup
client = genai.Client(api_key=GEMINI_API_KEY)


# 📁 Topics save karne ki file
TOPICS_FILE = "topics.json"


def generate_topics():
    """Gemini se 7 fresh Hinglish fact video topics generate karo"""

    prompt = """
    You are a content strategist for a viral Hinglish YouTube Shorts & Instagram Reels channel called "JanloYaar".
    
    The channel covers: Dark History, Mind-Blowing Science, Money & Power, Mystery & Conspiracy, Shocking World Facts.
    Audience: Hindi-speaking Indians aged 15-35.
    Style: Fun, energetic, shocking — like a friend telling you secrets.
    Format: 45-60 second short videos with text on screen (no voiceover).
    
    Generate exactly 7 unique, viral video topics in JSON format.
    Each topic must have:
    - "title": Hinglish title (mix of Hindi + English, shocking/curiosity-driven, max 10 words)
    - "pillar": one of [Science, Money & Power, Mystery, World Facts]
    - "hook": First line of the video (in Hinglish, must make viewer stop scrolling)
    - "why_viral": One line explaining why this topic will go viral
    
    Rules:
    - Topics must be unique and not repeated
    - Must be family-friendly but shocking
    - Mix all 5 pillars across the 7 topics
    - NO "kya tum jaante ho" for the hook line
    - Use shock + curiosity
    - Max 8 words title
    - Make people STOP scrolling
    
    Return ONLY a valid JSON array, no extra text.
    Example format:
    [
      {
        "title": "Woh desh jahan raat kabhi nahi aati",
        "pillar": "World Facts",
        "hook": "Soch ke dekho — ek jagah jahan suraj kabhi nahi duba!",
        "why_viral": "Norway midnight sun — relatable curiosity, easy to visualize"
      }
    ]
    """

    print("🤖 Gemini se topics generate ho rahe hain...")
    print("=" * 50)

    try:
        response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=prompt
)
        raw = response.text.strip()

        # Clean JSON if wrapped in markdown code block
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        topics = json.loads(raw)

        # Add metadata to each topic
        for i, topic in enumerate(topics):
            topic["id"] = i + 1
            topic["status"] = "pending"       # pending → scripted → filmed → uploaded
            topic["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            topic["scheduled_for"] = None

        return topics

    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"Raw response:\n{raw}")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def save_topics(topics):
    """Topics ko topics.json mein save karo"""

    # Load existing topics if file exists
    existing = []
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)

    # Fix IDs for new topics
    start_id = len(existing) + 1
    for i, topic in enumerate(topics):
        topic["id"] = start_id + i

    # Merge and save
    all_topics = existing + topics
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_topics, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(topics)} topics saved to {TOPICS_FILE}")
    return all_topics


def display_topics(topics):
    """Topics ko terminal mein display karo"""

    pillar_emojis = {
        "Dark History": "🕵️",
        "Science": "🧠",
        "Money & Power": "💰",
        "Mystery": "👁️",
        "World Facts": "🌍",
    }

    print("\n🔥 IS HAFTE KE 7 TOPICS — JANLO YAAR 🔥")
    print("=" * 55)

    for topic in topics:
        emoji = pillar_emojis.get(topic.get("pillar", ""), "📌")
        print(f"\n#{topic['id']} {emoji} [{topic['pillar']}]")
        print(f"   📌 Title  : {topic['title']}")
        print(f"   🎬 Hook   : {topic['hook']}")
        print(f"   🚀 Why    : {topic['why_viral']}")
        print(f"   📊 Status : {topic['status']}")

    print("\n" + "=" * 55)
    print(f"✅ Total topics in queue: {len(topics)}")


def get_pending_topics():
    """Sirf pending (not yet filmed) topics return karo"""

    if not os.path.exists(TOPICS_FILE):
        print("⚠️  topics.json nahi mila — pehle generate karo!")
        return []

    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        all_topics = json.load(f)

    pending = [t for t in all_topics if t["status"] == "pending"]
    return pending


def mark_topic_done(topic_id):
    """Ek topic ko 'uploaded' mark karo"""

    if not os.path.exists(TOPICS_FILE):
        return

    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        all_topics = json.load(f)

    for topic in all_topics:
        if topic["id"] == topic_id:
            topic["status"] = "uploaded"
            break

    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_topics, f, ensure_ascii=False, indent=2)

    print(f"✅ Topic #{topic_id} uploaded mark ho gaya!")


# ============================================================
#   MAIN — Directly run karo: python topic_generator.py
# ============================================================
if __name__ == "__main__":
    print("\n🚀 JANLO YAAR — Topic Generator")
    print("================================\n")

    # Step 1: Generate 7 new topics
    new_topics = generate_topics()

    if new_topics:
        # Step 2: Save to topics.json
        all_topics = save_topics(new_topics)

        # Step 3: Display in terminal
        display_topics(new_topics)

        print("\n💡 Next step: python script_writer.py")
    else:
        print("❌ Topics generate nahi hue. API key check karo!")
