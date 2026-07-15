import os
import json
import time
import schedule
from datetime import datetime

# ============================================================
#   JANLO YAAR — main.py (Master Runner)
#   Ek click mein sab kuch:
#   Topic → Script → Video → Metadata → Done!
# ============================================================

# ⚙️ Settings
AUTO_SCHEDULE   = False   # True karo agar daily auto-run chahiye
SCHEDULE_TIME   = "08:00" # Daily kitne baje run ho (24hr format)
TOPICS_FILE     = "topics.json"


# ============================================================
#   IMPORTS — sabhi modules yahan se call honge
# ============================================================
def import_modules():
    """Saare modules import karo — error aayi toh batao"""
    try:
        import topic_generator
        import script_generator
        import video_editor
        return topic_generator, script_generator, video_editor
    except ImportError as e:
        print(f"❌ Module import failed: {e}")
        print("   Confirm karo ki sab files ek hi folder mein hain!")
        exit()


# ============================================================
#   HELPER — Status check
# ============================================================
def get_counts():
    """topics.json se counts nikalo"""
    if not os.path.exists(TOPICS_FILE):
        return {"pending": 0, "scripted": 0, "filmed": 0, "uploaded": 0, "total": 0}

    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = json.load(f)

    return {
        "pending"  : len([t for t in topics if t["status"] == "pending"]),
        "scripted" : len([t for t in topics if t["status"] == "scripted"]),
        "filmed"   : len([t for t in topics if t["status"] == "filmed"]),
        "uploaded" : len([t for t in topics if t["status"] == "uploaded"]),
        "total"    : len(topics),
    }


def print_banner():
    print("\n" + "=" * 55)
    print("  🔥  JANLO YAAR — AUTOMATION MASTER  🔥")
    print("=" * 55)
    now = datetime.now().strftime("%d %b %Y | %I:%M %p")
    print(f"  📅 {now}")
    print("=" * 55)


def print_status():
    c = get_counts()
    print(f"\n📊 CURRENT STATUS:")
    print(f"   📌 Pending   : {c['pending']} topics")
    print(f"   ✍️  Scripted  : {c['scripted']} topics")
    print(f"   🎬 Filmed    : {c['filmed']} videos")
    print(f"   ✅ Uploaded  : {c['uploaded']} videos")
    print(f"   📁 Total     : {c['total']} topics")
    print()


def step_divider(step, title):
    print(f"\n{'='*55}")
    print(f"  STEP {step}: {title}")
    print(f"{'='*55}")


# ============================================================
#   CORE PIPELINE — Topic → Script → Video
# ============================================================
def run_pipeline():
    """Poora pipeline ek baar run karo"""

    print_banner()
    print_status()

    topic_generator, script_writer, video_editor = import_modules()
    c = get_counts()

    # ── STEP 1: Topics check / generate ──────────────────────
    step_divider(1, "TOPIC CHECK")

    if c["pending"] == 0:
        print("⚠️  Koi pending topic nahi — naye topics generate karta hoon...")
        time.sleep(1)
        new_topics = topic_generator.generate_topics()
        if new_topics:
            topic_generator.save_topics(new_topics)
            topic_generator.display_topics(new_topics)
            print(f"✅ {len(new_topics)} naye topics ready!")
        else:
            print("❌ Topics generate nahi hue! API key check karo.")
            return False
    else:
        print(f"✅ {c['pending']} pending topics already hain — skip generate!")

    time.sleep(1)

    # ── STEP 2: Script Write ──────────────────────────────────
    step_divider(2, "SCRIPT WRITER")

    topic = script_writer.load_next_topic()
    if not topic:
        print("❌ Koi topic nahi mila!")
        return False

    print(f"📌 Topic: {topic['title']}")
    script = script_writer.generate_script(topic)

    if not script:
        print("❌ Script generate nahi hua!")
        return False

    script_writer.save_script(script, topic["id"])
    script_writer.update_topic_status(topic["id"], "scripted")
    script_writer.display_script(script)

    time.sleep(1)

    # ── STEP 3: Video Edit ────────────────────────────────────
    step_divider(3, "VIDEO EDITOR")

    loaded_script = video_editor.load_script(topic["id"])
    if not loaded_script:
        return False

    # Image keywords generate karo
    print("🤖 Image keywords generate ho rahe hain...")
    keywords = video_editor.generate_image_keywords(loaded_script)

    # Har line ke liye image download + frame banao
    print(f"\n⬇️  {len(keywords)} images download ho rahi hain...")
    frame_paths = []

    for i, (line, keyword) in enumerate(zip(loaded_script["lines"], keywords)):
        print(f"  [{i+1}/{len(keywords)}] '{keyword}'...")
        bg_path    = video_editor.download_image(keyword, i)
        frame_img  = video_editor.create_frame(bg_path, line["text"], line["style"])
        frame_path = f"{video_editor.TEMP_DIR}/frame_{i}.jpg"
        frame_img.save(frame_path, quality=95)
        frame_paths.append(frame_path)

    print(f"✅ {len(frame_paths)} frames ready!")

    # Music skip — YouTube/Instagram pe add karenge
    music_path = None
    print("🎵 Music YouTube/Instagram pe upload ke time add karein!")

    # Video assemble karo
    video_path = video_editor.assemble_video(loaded_script, frame_paths, music_path)

    # Cleanup temp
    video_editor.cleanup_temp()

    # ── STEP 4: Metadata ──────────────────────────────────────
    step_divider(4, "METADATA GENERATE")

    metadata     = video_editor.generate_metadata(loaded_script)
    metadata_txt = video_editor.save_metadata(metadata, topic["id"])
    video_editor.display_metadata(metadata)

    # ── STEP 5: Status Update ─────────────────────────────────
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        all_topics = json.load(f)
    for t in all_topics:
        if t["id"] == topic["id"]:
            t["status"]    = "filmed"
            t["filmed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_topics, f, ensure_ascii=False, indent=2)

    # ── FINAL SUMMARY ─────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  🎉 PIPELINE COMPLETE — SAB KUCH READY!")
    print("=" * 55)
    print(f"\n  🎬 Video    : {video_path}")
    print(f"  📋 Metadata : {metadata_txt}")
    print(f"\n  📌 YouTube Title:")
    print(f"     {metadata['youtube_title']}")
    print(f"\n  ⏰ Best upload time: 7:30 AM – 8:30 AM")
    print(f"\n  👉 Ab manually upload karo yaar!")
    print("=" * 55)

    return True


# ============================================================
#   MENU — Interactive mode
# ============================================================
def show_menu():
    print("\n📋 KYA KARNA HAI?")
    print("  1️⃣  Ek video banao (full pipeline)")
    print("  2️⃣  Sirf naye topics generate karo")
    print("  3️⃣  Sirf script likho")
    print("  4️⃣  Current status dekho")
    print("  5️⃣  Auto daily scheduler start karo")
    print("  0️⃣  Exit")
    print()
    return input("  Choice daalo (0-5): ").strip()


def only_topics():
    topic_generator, _, _ = import_modules()
    print("\n🤖 Naye topics generate ho rahe hain...")
    new_topics = topic_generator.generate_topics()
    if new_topics:
        topic_generator.save_topics(new_topics)
        topic_generator.display_topics(new_topics)


def only_script():
    _, script_writer, _ = import_modules()
    topic = script_writer.load_next_topic()
    if not topic:
        return
    script = script_writer.generate_script(topic)
    if script:
        script_writer.save_script(script, topic["id"])
        script_writer.update_topic_status(topic["id"], "scripted")
        script_writer.display_script(script)


def start_scheduler():
    print(f"\n⏰ Daily scheduler start ho raha hai — {SCHEDULE_TIME} baje run karega!")
    print("   Band karne ke liye Ctrl+C dabaao\n")

    schedule.every().day.at(SCHEDULE_TIME).do(run_pipeline)

    while True:
        schedule.run_pending()
        now = datetime.now().strftime("%H:%M:%S")
        print(f"  ⏳ {now} — Next run: {SCHEDULE_TIME} | Ctrl+C to stop", end="\r")
        time.sleep(30)


# ============================================================
#   MAIN
# ============================================================
if __name__ == "__main__":

    # Install schedule agar nahi hai
    try:
        import schedule
    except ImportError:
        print("📦 'schedule' library install ho rahi hai...")
        os.system("py -3.11 -m pip install schedule")
        import schedule

    print_banner()
    print_status()

    while True:
        choice = show_menu()

        if choice == "1":
            run_pipeline()

        elif choice == "2":
            only_topics()

        elif choice == "3":
            only_script()

        elif choice == "4":
            print_banner()
            print_status()

        elif choice == "5":
            start_scheduler()

        elif choice == "0":
            print("\n👋 Bye Atul! Kal phir milenge yaar! 🔥")
            break

        else:
            print("❌ Invalid choice — 0 se 5 ke beech daalo!")

        print("\n" + "-" * 55)
        input("  Enter dabaao menu pe wapas jaane ke liye...")
