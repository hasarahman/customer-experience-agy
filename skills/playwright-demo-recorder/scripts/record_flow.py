#!/usr/bin/env python3
"""Autonomous Playwright Demo Video Recorder.

Executes automated, human-paced browser interaction flows and records
high-definition demo videos (WebM/MP4) for AI agents and web apps.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


def type_slowly(page, selector: str, text: str, delay: float = 0.04):
    """Types text into an input field with realistic human keystroke intervals."""
    page.click(selector)
    page.fill(selector, "")
    for char in text:
        page.type(selector, char, delay=int(delay * 1000))


def wait_for_agent_reply(
    page,
    message_selector: str,
    expected_count: int,
    thinking_selector: str = None,
    timeout: float = 45.0,
):
    """Waits for the agent to finish thinking and render the expected message count."""
    start_time = time.monotonic()
    while time.monotonic() - start_time < timeout:
        current_count = page.locator(message_selector).count()
        if current_count >= expected_count:
            if thinking_selector:
                is_thinking_visible = (
                    page.locator(thinking_selector).count() > 0
                    and page.locator(thinking_selector).is_visible()
                )
                if is_thinking_visible:
                    time.sleep(0.3)
                    continue
            time.sleep(0.5)
            return True
        time.sleep(0.3)
    raise TimeoutError(
        f"Timed out after {timeout}s waiting for {message_selector} count >= {expected_count}"
    )


class DemoRecorder:
    def __init__(
        self,
        output_dir: str = "demo_recordings",
        video_name: str = "demo.webm",
        width: int = 1280,
        height: int = 820,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.video_name = video_name
        self.width = width
        self.height = height

    def record_scenario(self, scenario_config: dict) -> Path:
        """Executes a scenario configuration dict using Playwright."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            sys.exit(
                "Error: Playwright is not installed. Install via: pip install playwright && playwright install chromium"
            )

        target_url = scenario_config.get("url", "http://127.0.0.1:8080")
        input_sel = scenario_config.get("input_selector", "#userInput")
        send_sel = scenario_config.get("send_selector", "#sendBtn")
        msg_sel = scenario_config.get("message_selector", ".agent-message")
        thinking_sel = scenario_config.get("thinking_selector", ".thinking-indicator")
        turns = scenario_config.get("turns", [])

        print("=" * 65)
        print(f"🎬 Starting Autonomous Live Demo Recording")
        print(f"🌐 Target URL: {target_url}")
        print(f"📁 Video Output Dir: {self.output_dir.resolve()}")
        print(f"🖥️ Dimensions: {self.width}x{self.height}")
        print("=" * 65)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                record_video_dir=str(self.output_dir),
                record_video_size={"width": self.width, "height": self.height},
                viewport={"width": self.width, "height": self.height},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            )
            page = context.new_page()

            print(f"\n🌐 Loading web app: {target_url}...")
            page.goto(target_url)
            page.wait_for_load_state("networkidle")
            time.sleep(scenario_config.get("initial_pause", 2.0))

            agent_turn_count = 0

            for idx, turn in enumerate(turns, start=1):
                user_text = turn.get("user")
                action_type = turn.get("action", "chat")
                desc = turn.get("desc", f"Turn {idx}")
                typing_delay = turn.get("typing_delay", 0.04)
                pre_send_pause = turn.get("pre_send_pause", 0.7)
                read_pause = turn.get("read_pause", 4.0)

                print(f"\n💬 [Step {idx}/{len(turns)}] {desc}")

                if action_type == "chat" and user_text is not None:
                    print(f"   ⌨️  Typing: \"{user_text}\"")
                    type_slowly(page, input_sel, user_text, delay=typing_delay)
                    time.sleep(pre_send_pause)

                    print(f"   🖱️  Clicking send...")
                    page.click(send_sel)
                    agent_turn_count += 1

                    print(f"   ⏳ Waiting for agent reply #{agent_turn_count}...")
                    wait_for_agent_reply(
                        page,
                        message_selector=msg_sel,
                        expected_count=agent_turn_count,
                        thinking_selector=thinking_sel,
                        timeout=turn.get("timeout", 45.0),
                    )
                    print(f"   ✅ Agent response received! Pausing {read_pause}s for readability...")
                    time.sleep(read_pause)

                elif action_type == "click":
                    target_btn = turn.get("selector")
                    print(f"   🖱️  Clicking selector: {target_btn}")
                    page.click(target_btn)
                    time.sleep(turn.get("pause", 2.0))

                elif action_type == "pause":
                    pause_sec = turn.get("duration", 3.0)
                    print(f"   ⏸️  Pausing for {pause_sec}s...")
                    time.sleep(pause_sec)

            # Final showcase window
            final_pause = scenario_config.get("final_pause", 6.0)
            print(f"\n🏁 Final showcase pause ({final_pause}s)...")
            time.sleep(final_pause)

            # Close context to flush video to disk
            raw_video = page.video.path() if page.video else None
            context.close()
            browser.close()

            final_dest = self.output_dir / self.video_name
            if raw_video and os.path.exists(raw_video):
                os.replace(raw_video, final_dest)
                print(f"\n🎉 Video recorded successfully: {final_dest} ({final_dest.stat().st_size // 1024} KB)")

                # Automatic MP4 conversion for maximum cross-platform & social media compatibility
                mp4_dest = final_dest.with_suffix(".mp4")
                try:
                    import subprocess
                    try:
                        import imageio_ffmpeg
                        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                    except ImportError:
                        ffmpeg_exe = "ffmpeg"

                    print(f"🎬 Converting to MP4 using FFmpeg...")
                    cmd = [
                        ffmpeg_exe, "-y", "-i", str(final_dest),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-preset", "medium", "-crf", "20",
                        "-movflags", "+faststart", str(mp4_dest)
                    ]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"✅ Generated MP4: {mp4_dest} ({mp4_dest.stat().st_size // 1024} KB)")
                except Exception as e:
                    print(f"⚠️ MP4 conversion skipped: {e}")

                return final_dest
            else:
                raise FileNotFoundError(f"Video file was not generated by Playwright.")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Playwright Demo Video Recorder")
    parser.add_argument("--scenario", required=True, help="Path to JSON scenario configuration file")
    parser.add_argument("--output-dir", default="demo_recordings", help="Output directory for recordings")
    parser.add_argument("--video-name", default="demo.webm", help="File name of the final recorded video")
    parser.add_argument("--width", type=int, default=1280, help="Viewport width in pixels")
    parser.add_argument("--height", type=int, default=820, help="Viewport height in pixels")
    args = parser.parse_args()

    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        sys.exit(f"Error: Scenario file '{args.scenario}' not found.")

    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario_data = json.load(f)

    recorder = DemoRecorder(
        output_dir=args.output_dir,
        video_name=args.video_name,
        width=args.width,
        height=args.height,
    )
    recorder.record_scenario(scenario_data)


if __name__ == "__main__":
    main()
