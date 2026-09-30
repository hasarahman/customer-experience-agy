---
name: playwright-demo-recorder
description: >-
  Record autonomous, high-definition web UI demo videos of AI agents and web apps using Playwright.
  Includes automated pre-flight testing, human-like typing simulation, smooth cadence,
  WebM generation, and interactive generative UI video player embedding.
---

# Playwright Demo Recorder

The `playwright-demo-recorder` skill automates the creation of high-definition, human-paced browser demo videos for AI agents, customer experiences, and web applications. It replaces error-prone manual screen recording with deterministic, repeatable Playwright automation.

---

## When to Use

Activate this skill when:
- Creating video demonstrations of conversational AI agents (e.g. Google ADK, FastAPI, LangGraph).
- Recording multi-turn customer journeys (order lookup, OTP verification, RAG knowledge retrieval).
- Documenting software releases, LinkedIn product showcases, or team demos.
- Needing deterministic browser automation that types with realistic human cadence and pauses.

---

## Architecture & Workflow

```
┌────────────────────────────────────────────────────────┐
│ Phase 1: Pre-Flight Verification ("Test Before Record")│
│ • Execute multi-turn assertion harness against live API │
│ • Verify tool calls, status codes, and message semantics│
└──────────────────────────┬─────────────────────────────┘
                           │ 100% Passes
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 2: Local UI & Daemon Management                  │
│ • Launch web chat server / proxy on designated port    │
│ • Enforce event chunk deduplication for streaming UIs  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 3: Autonomous Playwright Recording               │
│ • Headless Chromium at 1280x820 HD                     │
│ • Human-like keystroke intervals (30-50ms)             │
│ • Deliberation pauses & comprehension windows          │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 4: Artifact Generation & Delivery                │
│ • Save .webm in demo directory and brain artifacts     │
│ • Generate theme-adaptive HTML5 player (<agent-embed>) │
│ • Open in Google Chrome & highlight in macOS Finder    │
└────────────────────────────────────────────────────────┘
```

---

## Golden Rules

### 1. "Test It Before We Record"
**Never record blind.** If an agent prompt or backend code changed:
1. Deploy or start the service revision.
2. Run an automated test harness (`test_live_flow.py`) validating all user turns and tool assertions before recording.
3. If an assertion fails, fix the agent/backend first. Do not waste time recording a broken flow.

### 2. Natural Human Cadence
Fast machine interactions look robotic and are impossible for humans to follow in a video. Enforce these timing standards:
- **Keystroke typing**: `30ms – 50ms` per character (`type_slowly`).
- **Pre-send deliberation**: `500ms – 800ms` pause after typing before clicking Send.
- **Reading comprehension**: `3.5s – 5.0s` pause after agent responses so viewers can comfortably read the answer.
- **Finale showcase**: `6.0s – 8.0s` pause at the end showing the full conversation state.

### 3. Stream Chunk Deduplication
Streaming agent backends (like Google ADK `/run` event streams) emit separate events before and after tool calls. If client UI code naively concatenates text from every chunk event without deduplicating identical paragraphs, message bubbles will repeat.
Always check:
```python
if clean_text not in reply_parts:
    reply_parts.append(clean_text)
```

### 4. Sandbox Awareness & Authentication
When running scripts that fetch Google Cloud identity tokens (`gcloud auth print-identity-token`) or contact external Cloud Run services, run commands with `BypassSandbox: true` so network authentication does not fail.

---

## Quick Start: Using the Bundled Scripts

The skill provides two production-ready helper scripts located in `scripts/`:

### 1. Record a Scenario (`record_flow.py`)
Define your scenario in a JSON file (see `references/scenario_template.json`):

```json
{
  "url": "http://127.0.0.1:8085",
  "input_selector": "#userInput",
  "send_selector": "#sendBtn",
  "message_selector": ".agent-message",
  "turns": [
    {"user": "Hi", "read_pause": 3.5},
    {"user": "I lost my order number", "read_pause": 4.0},
    {"user": "user@example.com", "read_pause": 3.5},
    {"user": "123456", "read_pause": 4.5}
  ]
}
```

Run the recorder:
```bash
python3 ~/.gemini/config/skills/playwright-demo-recorder/scripts/record_flow.py \
  --scenario scenario.json \
  --output-dir demo_recordings \
  --video-name live_demo.webm \
  --width 1280 \
  --height 820
```

### 2. Generate Interactive Player Artifact (`generate_player.py`)
Package the video into an HTML5 player with Tailwind CSS:

```bash
python3 ~/.gemini/config/skills/playwright-demo-recorder/scripts/generate_player.py \
  --video demo_recordings/live_demo.webm \
  --output video_player.html \
  --title "Customer Experience Agent Demo" \
  --subtitle "Cloud Run &bull; Firestore &bull; Agent Platform RAG" \
  --highlight "<b>1. Reverse Lookup:</b> Email fallback when order number is lost" \
  --highlight "<b>2. OTP Verification:</b> 6-digit Firestore security challenge" \
  --highlight "<b>3. Grounded Policy:</b> 30-day return policy answered via RAG"
```

### 3. Display and Open
In Antigravity chat, embed the player inline:
```html
<agent-embed src="file:///path/to/video_player.html"></agent-embed>
```

Launch directly in Google Chrome and macOS Finder:
```bash
open -a "Google Chrome" video_player.html
open -R demo_recordings/live_demo.webm
```

---

## Reference Implementation Pattern

For custom recording flows requiring fine-grained assertions or non-standard UI controls, follow this standard Python pattern:

```python
import time
from playwright.sync_api import sync_playwright

def record_custom_demo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="demo_recordings",
            record_video_size={"width": 1280, "height": 820},
            viewport={"width": 1280, "height": 820},
        )
        page = context.new_page()
        page.goto("http://127.0.0.1:8085")
        time.sleep(2.0)

        # Step: Type slowly
        page.click("#userInput")
        for char in "hasan2296@outlook.com":
            page.type("#userInput", char, delay=40)
        time.sleep(0.7)

        page.click("#sendBtn")
        
        # Wait for agent response
        page.wait_for_selector(".agent-message:nth-child(4)", timeout=45000)
        time.sleep(4.0)

        context.close()
        browser.close()
```

---

## Common Pitfalls & Troubleshooting

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Video is black or 0 bytes** | Browser context closed abruptly before flushing video stream | Always call `context.close()` and `browser.close()` cleanly. |
| **Text types instantly** | Standard `fill()` replaces input value in a single frame | Use `page.type(selector, char, delay=40)` in a loop. |
| **Agent bubbles repeat identical text** | Backend SSE / ADK event stream delivers duplicate chunks | Deduplicate chunk text before appending to DOM in the web client. |
| **`gcloud auth` exits with code 1** | Sandbox network restrictions | Run commands with `BypassSandbox: true` when communicating with Cloud APIs. |
| **Port already in use (`Address already in use`)** | Previous server daemon still running | Use `manage_task` with action `kill` or run `lsof -ti :<port> \| xargs kill -9`. |
