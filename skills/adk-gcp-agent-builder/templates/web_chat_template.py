"""Zero-Dependency Web Chat UI for ADK Cloud Run Services.

Runs a local web server (default port 8085) with an interactive chat interface,
automatically authenticates to Cloud Run using 'gcloud auth print-identity-token',
and creates/manages ADK sessions.
"""

import http.server
import json
import os
import socketserver
import subprocess
import urllib.request
import webbrowser

PORT = int(os.environ.get("WEB_CHAT_PORT", "8085"))
CLOUD_RUN_URL = os.environ.get("CLOUD_RUN_URL", "http://127.0.0.1:8080")
APP_NAME = os.environ.get("ADK_APP_NAME", "app")
USER_ID = os.environ.get("ADK_USER_ID", "test-user")


def get_token() -> str:
    """Fetch identity token from gcloud CLI."""
    try:
        return subprocess.check_output(
            ["gcloud", "auth", "print-identity-token"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return ""


SESSION_CACHE = {}


def get_or_create_session(token: str) -> str:
    """Create or reuse an ADK session ID."""
    if "session_id" in SESSION_CACHE:
        return SESSION_CACHE["session_id"]

    url = f"{CLOUD_RUN_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=b"", headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            SESSION_CACHE["session_id"] = data["id"]
            return data["id"]
    except Exception as e:
        print(f"Failed to create remote session: {e}. Falling back to default ID.")
        SESSION_CACHE["session_id"] = "session_001"
        return "session_001"


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ADK Agent — Live Chat</title>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Google Sans', sans-serif;
      background: #f0f4f9;
      height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .chat-container {
      width: 100%;
      max-width: 750px;
      height: 85vh;
      background: white;
      border-radius: 16px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .chat-header {
      background: linear-gradient(135deg, #1a73e8, #4285f4);
      color: white;
      padding: 18px 24px;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .badge {
      background: #34a853;
      color: white;
      font-size: 11px;
      font-weight: 500;
      padding: 3px 8px;
      border-radius: 12px;
      margin-left: auto;
    }
    .messages {
      flex: 1;
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .msg {
      max-width: 80%;
      padding: 12px 18px;
      border-radius: 16px;
      font-size: 14.5px;
      line-height: 1.5;
      white-space: pre-wrap;
    }
    .msg.agent { background: #f1f3f4; color: #202124; align-self: flex-start; }
    .msg.user { background: #1a73e8; color: white; align-self: flex-end; }
    .tool-tag {
      font-size: 11px;
      color: #5f6368;
      background: #e8eaed;
      padding: 2px 6px;
      border-radius: 4px;
      margin-top: 6px;
      display: inline-block;
    }
    .input-box {
      display: flex;
      padding: 16px 24px;
      border-top: 1px solid #e0e0e0;
      background: #fafafa;
      gap: 12px;
    }
    .input-box input {
      flex: 1;
      padding: 12px 16px;
      border: 1px solid #dadce0;
      border-radius: 24px;
      outline: none;
      font-size: 14.5px;
    }
    .input-box button {
      background: #1a73e8;
      color: white;
      border: none;
      padding: 0 24px;
      border-radius: 24px;
      font-weight: 500;
      cursor: pointer;
    }
    .input-box button:hover { background: #1557b0; }
  </style>
</head>
<body>
  <div class="chat-container">
    <div class="chat-header">
      <div style="font-size: 24px;">🤖</div>
      <div>
        <h2 style="font-size: 18px; font-weight: 500;">ADK Agent — Live Chat</h2>
        <div style="font-size: 12px; opacity: 0.9;">GCP-Native • Cloud Run • Firestore • Agent Platform</div>
      </div>
      <div class="badge">Connected 🟢</div>
    </div>
    
    <div class="messages" id="msgs">
      <div class="msg agent">👋 Hi! I'm your AI Virtual Assistant. How can I help you today?</div>
    </div>

    <form class="input-box" onsubmit="sendMessage(event)">
      <input type="text" id="userInput" placeholder="Type a message..." autocomplete="off" autofocus />
      <button type="submit" id="sendBtn">Send</button>
    </form>
  </div>

  <script>
    async function sendMessage(e) {
      if (e) e.preventDefault();
      const input = document.getElementById('userInput');
      const text = input.value.trim();
      if (!text) return;
      
      const msgs = document.getElementById('msgs');
      msgs.innerHTML += `<div class="msg user">${text}</div>`;
      input.value = '';
      msgs.scrollTop = msgs.scrollHeight;

      const loadingId = 'loading-' + Date.now();
      msgs.innerHTML += `<div class="msg agent" id="${loadingId}">Thinking...</div>`;
      msgs.scrollTop = msgs.scrollHeight;

      try {
        const resp = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: text})
        });
        const data = await resp.json();
        const loadElem = document.getElementById(loadingId);
        
        let toolHtml = '';
        if (data.tools && data.tools.length > 0) {
          toolHtml = `<br><span class="tool-tag">🔧 Called: ${data.tools.join(', ')}</span>`;
        }
        loadElem.innerHTML = data.reply + toolHtml;
      } catch (err) {
        document.getElementById(loadingId).innerText = 'Error: ' + err.message;
      }
      msgs.scrollTop = msgs.scrollHeight;
    }
  </script>
</body>
</html>
"""


class ChatHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode())

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode())
        user_message = body.get("message", "")

        token = get_token()
        session_id = get_or_create_session(token)

        payload = {
            "appName": APP_NAME,
            "userId": USER_ID,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": user_message}],
            },
        }

        run_url = f"{CLOUD_RUN_URL}/run"
        headers = {
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(
            run_url,
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )

        reply_text = ""
        tools_called = []

        try:
            with urllib.request.urlopen(req) as resp:
                events = json.loads(resp.read().decode())
                for event in events:
                    for part in event.get("content", {}).get("parts", []):
                        if "text" in part:
                            reply_text += part["text"]
                        if "functionCall" in part:
                            tools_called.append(part["functionCall"]["name"])
        except Exception as e:
            reply_text = f"Backend Error: {e}"

        response_data = {"reply": reply_text, "tools": tools_called}
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())


def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), ChatHandler) as httpd:
        print(f"ADK Web Chat UI running at http://127.0.0.1:{PORT}")
        print(f"Targeting Cloud Run service: {CLOUD_RUN_URL}")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
