#!/usr/bin/env python3
"""Autonomous Demo Recorder for Customer Experience Agent (Rainbow).

Interacts live with the Web Chat UI connected to Cloud Run and records a
high-definition video (.webm and .mp4) of the entire session.
"""

import os
import subprocess
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "demo_recordings")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FFMPEG_PATH = os.path.expanduser("~/Library/Caches/ms-playwright/ffmpeg-1011/ffmpeg-mac")


def type_slowly(page, selector, text, delay=0.04):
    """Simulates natural, human-like typing."""
    for char in text:
        page.type(selector, char, delay=int(delay * 1000))
        time.sleep(delay)


def reset_session():
    """Resets the server-side Cloud Run session so demo starts fresh."""
    try:
        req = urllib.request.Request("http://127.0.0.1:8085/api/reset", data=b"{}", method="POST")
        with urllib.request.urlopen(req) as resp:
            pass
    except Exception as e:
        print(f"Warning resetting session: {e}")


def convert_to_mp4(webm_path, mp4_path):
    """Converts recorded .webm video to universal .mp4 for LinkedIn/social."""
    if os.path.exists(FFMPEG_PATH):
        print(f"🎬 Converting {os.path.basename(webm_path)} to MP4 using FFmpeg...")
        cmd = [
            FFMPEG_PATH,
            "-y",
            "-i",
            webm_path,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "fast",
            "-crf",
            "22",
            mp4_path,
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"✅ MP4 Video Generated: {mp4_path} ({os.path.getsize(mp4_path) // 1024} KB)")
            return True
        except Exception as e:
            print(f"FFmpeg conversion warning: {e}")
            return False
    return False


def wait_for_agent_reply(page, expected_agent_count, timeout=40):
    """Waits for the agent to finish thinking and render its reply."""
    start = time.time()
    while time.time() - start < timeout:
        count = page.locator(".msg.agent:not(#loading)").count()
        disabled = page.eval_on_selector("#sendBtn", "el => el.disabled")
        if count >= expected_agent_count and not disabled:
            return True
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for agent message #{expected_agent_count}")


def run_recording(headless=True):
    print("=" * 65)
    print("🎬 Starting Autonomous Live Cloud Run Demo Recording")
    print(f"📁 Video Directory: {OUTPUT_DIR}")
    print(f"🖥️ Mode: {'Headless (Video Export)' if headless else 'Visible Screen'}")
    print("=" * 65)

    reset_session()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=headless,
            slow_mo=25,
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 820},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1280, "height": 820},
        )

        page = context.new_page()

        print("\n🌐 [Step 1/5] Opening Customer Experience Web Chat...")
        page.goto("http://127.0.0.1:8085")
        page.wait_for_selector("#msgs", timeout=10000)
        time.sleep(2.5)

        # ---------------------------------------------------------
        # Turn 1: Friendly Greeting
        # ---------------------------------------------------------
        print("\n💬 [Turn 1/5] Greeting Rainbow...")
        query_1 = "Hi"
        type_slowly(page, "#userInput", query_1, delay=0.04)
        time.sleep(0.7)

        page.click("#sendBtn")
        print("   ⏳ Waiting for Rainbow greeting...")
        wait_for_agent_reply(page, expected_agent_count=1)
        print("   ✅ Rainbow greeted the user!")
        time.sleep(3.5)

        # ---------------------------------------------------------
        # Turn 2: Lost Order Number Inquiry
        # ---------------------------------------------------------
        print("\n💬 [Turn 2/5] Reporting lost order number...")
        query_2 = "I haven't received my order yet, can you check on my order? I lost my order number."
        type_slowly(page, "#userInput", query_2, delay=0.035)
        time.sleep(0.7)

        page.click("#sendBtn")
        print("   ⏳ Waiting for reverse lookup offer...")
        wait_for_agent_reply(page, expected_agent_count=2)
        print("   ✅ Rainbow offered email reverse lookup!")
        time.sleep(3.5)

        # ---------------------------------------------------------
        # Turn 3: Provide Email Address (Triggers OTP Auth)
        # ---------------------------------------------------------
        print("\n💬 [Turn 3/6] Providing account email (hasan2296@outlook.com)...")
        query_3 = "hasan2296@outlook.com"
        type_slowly(page, "#userInput", query_3, delay=0.04)
        time.sleep(0.7)

        page.click("#sendBtn")
        print("   ⏳ Cloud Run executing send_auth_code in Firestore...")
        wait_for_agent_reply(page, expected_agent_count=3)
        print("   ✅ Rainbow generated OTP and requested 6-digit code!")
        time.sleep(3.5)

        # ---------------------------------------------------------
        # Turn 4: Provide OTP Verification Code
        # ---------------------------------------------------------
        print("\n💬 [Turn 4/6] Entering 6-digit OTP code (123456)...")
        query_4 = "123456"
        type_slowly(page, "#userInput", query_4, delay=0.06)
        time.sleep(0.7)

        page.click("#sendBtn")
        print("   ⏳ Cloud Run executing verify_auth_code & find_orders_by_email...")
        wait_for_agent_reply(page, expected_agent_count=4)
        print("   ✅ Identity verified! Rainbow listed orders and asked to choose book!")
        time.sleep(4.5)

        # ---------------------------------------------------------
        # Turn 5: Disambiguate by Book Title
        # ---------------------------------------------------------
        print("\n💬 [Turn 5/6] Selecting book: Project Hail Mary...")
        query_5 = "Project Hail Mary"
        type_slowly(page, "#userInput", query_5, delay=0.04)
        time.sleep(0.7)

        page.click("#sendBtn")
        print("   ⏳ Cloud Run checking delivery status with lookup_order...")
        wait_for_agent_reply(page, expected_agent_count=5)
        print("   ✅ Rainbow reported 'Processing' delivery status!")
        time.sleep(4.5)

        # ---------------------------------------------------------
        # Turn 6: Grounded Policy Question (Return Window)
        # ---------------------------------------------------------
        print("\n💬 [Turn 6/6] Inquiring about return window...")
        query_6 = "whats your return window?"
        type_slowly(page, "#userInput", query_6, delay=0.035)
        time.sleep(0.7)

        page.click("#sendBtn")
        print("   ⏳ Cloud Run executing search_policy_kb via Agent Platform RAG...")
        wait_for_agent_reply(page, expected_agent_count=6)
        print("   ✅ Rainbow answered 30-day policy concisely!")
        time.sleep(6.5)  # Showcase complete conversation

        print("\n🏁 Finalizing and saving high-definition video...")
        page_video = page.video
        raw_video_path = page_video.path() if page_video else None
        context.close()
        browser.close()

        final_webm = os.path.join(OUTPUT_DIR, "customer_experience_agent_live_demo.webm")
        final_mp4 = os.path.join(OUTPUT_DIR, "customer_experience_agent_live_demo.mp4")

        if raw_video_path and os.path.exists(raw_video_path):
            if os.path.exists(final_webm):
                os.remove(final_webm)
            os.rename(raw_video_path, final_webm)

            print("\n" + "=" * 65)
            print("🎉 DEMO VIDEO RECORDED SUCCESSFULLY!")
            print(f"📹 WebM Video: {final_webm} ({os.path.getsize(final_webm) // 1024} KB)")

            convert_to_mp4(final_webm, final_mp4)
            print("=" * 65)
            return final_mp4 if os.path.exists(final_mp4) else final_webm
        else:
            print("⚠️ No video path returned.")
            return None


if __name__ == "__main__":
    is_headless = "--visible" not in sys.argv
    run_recording(headless=is_headless)
