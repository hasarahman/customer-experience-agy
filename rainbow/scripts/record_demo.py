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
        req = urllib.request.Request("http://localhost:8085/api/reset", data=b"{}", method="POST")
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
        page.goto("http://localhost:8085")
        page.wait_for_selector("#msgs", timeout=10000)
        time.sleep(2.5)

        # ---------------------------------------------------------
        # Turn 1: Grounded RAG Query (Return Policy)
        # ---------------------------------------------------------
        print("\n💬 [Step 2/5] Asking policy question (testing Agent Platform RAG)...")
        query_1 = "What is your return policy and window?"
        type_slowly(page, "#userInput", query_1, delay=0.035)
        time.sleep(0.7)

        page.click("#sendBtn")
        print("   ⏳ Cloud Run executing search_policy_kb...")
        wait_for_agent_reply(page, expected_agent_count=2)
        print("   ✅ Received grounded RAG answer from Cloud Run!")
        time.sleep(4.5)  # Let viewer read response

        # ---------------------------------------------------------
        # Turn 2: Identity-Gated Order Request
        # ---------------------------------------------------------
        print("\n💬 [Step 3/5] Requesting order lookup for hasan2296@outlook.com...")
        query_2 = "Can you check order BK-10001 for hasan2296@outlook.com?"
        type_slowly(page, "#userInput", query_2, delay=0.035)
        time.sleep(0.7)

        page.click("#sendBtn")
        print("   ⏳ Waiting for identity verification prompt...")
        wait_for_agent_reply(page, expected_agent_count=3)
        print("   ✅ Agent requested confirmation to send OTP code.")
        time.sleep(3.0)

        # ---------------------------------------------------------
        # Turn 3: Confirm Email to Trigger send_auth_code
        # ---------------------------------------------------------
        print("\n💬 [Step 4/5] Confirming email to trigger send_auth_code in Firestore...")
        query_3 = "Yes, please send the code to hasan2296@outlook.com"
        type_slowly(page, "#userInput", query_3, delay=0.035)
        time.sleep(0.7)

        page.click("#sendBtn")
        print("   ⏳ Cloud Run generating OTP in Firestore...")
        wait_for_agent_reply(page, expected_agent_count=4)
        print("   ✅ OTP sent to customer email!")
        time.sleep(3.0)

        # ---------------------------------------------------------
        # Turn 4: Enter 6-digit OTP Code
        # ---------------------------------------------------------
        print("\n💬 [Step 5/5] Entering 6-digit OTP code (123456)...")
        otp_code = "123456"
        type_slowly(page, "#userInput", otp_code, delay=0.08)
        time.sleep(0.7)

        page.click("#sendBtn")
        print("   ⏳ Cloud Run verifying OTP and looking up order BK-10001...")
        wait_for_agent_reply(page, expected_agent_count=5)
        print("   ✅ Identity verified! Order BK-10001 displayed successfully.")
        time.sleep(6.5)  # Showcase final verified conversation state

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
