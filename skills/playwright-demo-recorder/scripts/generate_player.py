#!/usr/bin/env python3
"""HTML5 Interactive Video Player Generator.

Embeds recorded demo videos (WebM/MP4) into a standalone, theme-adaptive
HTML player suitable for Antigravity <agent-embed> inline rendering or
direct viewing in Chrome.
"""

import argparse
import base64
import os
import sys
from pathlib import Path


def generate_player_html(
    video_path: str,
    output_html: str,
    title: str = "AI Agent Live Demo",
    subtitle: str = "Autonomous Playwright Session &bull; HD Video",
    highlights: list = None,
) -> Path:
    video_file = Path(video_path)
    if not video_file.exists():
        sys.exit(f"Error: Video file '{video_path}' does not exist.")

    mime_type = "video/mp4" if video_file.suffix.lower() == ".mp4" else "video/webm"
    file_size_kb = video_file.stat().st_size // 1024

    with open(video_file, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("utf-8")

    highlights_html = ""
    if highlights:
        cards = []
        for h in highlights:
            cards.append(
                f'<div class="p-2.5 rounded-lg bg-[var(--background,#f8fafc)] border border-[var(--border,#e2e8f0)] text-xs text-[var(--muted-foreground,#64748b)]">'
                f'{h}'
                f'</div>'
            )
        highlights_html = f'<div class="mt-4 grid grid-cols-1 md:grid-cols-{min(len(cards), 3)} gap-2">' + "".join(cards) + '</div>'

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
</head>
<body class="bg-transparent text-[var(--foreground,#0f172a)] antialiased p-3 sm:p-5 flex flex-col items-center justify-center">
  <div class="bg-[var(--card,#ffffff)] text-[var(--foreground,#0f172a)] border border-[var(--border,#e2e8f0)] rounded-2xl p-4 sm:p-5 shadow-lg w-full max-w-4xl">
    <div class="flex items-center justify-between mb-3">
      <div>
        <h2 class="text-base sm:text-lg font-bold flex items-center gap-2">
          <span>🎬</span> {title}
        </h2>
        <p class="text-xs text-[var(--muted-foreground,#64748b)]">
          {subtitle} &bull; {file_size_kb} KB
        </p>
      </div>
      <span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
        Recorded Live
      </span>
    </div>
    
    <div class="overflow-hidden rounded-xl border border-[var(--border,#e2e8f0)] bg-black shadow-inner">
      <video controls autoplay muted playsinline class="w-full h-auto rounded-xl" style="max-height: 520px;">
        <source src="data:{mime_type};base64,{b64_data}" type="{mime_type}">
        Your browser does not support the video tag.
      </video>
    </div>

    {highlights_html}
  </div>
</body>
</html>"""

    out_path = Path(output_html)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Generated interactive player: {out_path.resolve()} ({out_path.stat().st_size // 1024} KB)")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate interactive HTML5 player for recorded videos")
    parser.add_argument("--video", required=True, help="Path to WebM or MP4 video file")
    parser.add_argument("--output", required=True, help="Path for destination HTML file")
    parser.add_argument("--title", default="AI Agent Live Demo", help="Title for the player")
    parser.add_argument("--subtitle", default="Autonomous Session &bull; Playwright HD", help="Subtitle metadata")
    parser.add_argument("--highlight", action="append", help="Feature highlight card (can repeat)")
    args = parser.parse_args()

    generate_player_html(
        video_path=args.video,
        output_html=args.output,
        title=args.title,
        subtitle=args.subtitle,
        highlights=args.highlight,
    )


if __name__ == "__main__":
    main()
