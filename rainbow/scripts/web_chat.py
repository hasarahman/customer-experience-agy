#!/usr/bin/env python3
"""Standalone Customer Experience Web Chat Server connecting directly to Cloud Run."""

import http.server
import json
import os
import socketserver
import subprocess
import urllib.request
import webbrowser

PORT = 8085
CLOUD_RUN_URL = "https://rainbow-agent-642781268620.us-central1.run.app"


def get_token():
    return (
        subprocess.check_output(
            ["gcloud", "auth", "print-identity-token"], stderr=subprocess.DEVNULL
        )
        .decode()
        .strip()
    )


SESSION_CACHE = {}


def get_or_create_session(token):
    if "session_id" in SESSION_CACHE:
        return SESSION_CACHE["session_id"]
    url = f"{CLOUD_RUN_URL}/apps/app/users/hasan-rahman/sessions"
    req = urllib.request.Request(
        url,
        data=b"",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        SESSION_CACHE["session_id"] = data["id"]
        return data["id"]


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Customer Experience — Rainbow Agent</title>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;500&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Google Sans', 'Roboto', sans-serif;
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
      line-height: 1.5;
      font-size: 14.5px;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .msg.user {
      align-self: flex-end;
      background: #e8f0fe;
      color: #1967d2;
      border-bottom-right-radius: 4px;
    }
    .msg.agent {
      align-self: flex-start;
      background: #f8f9fa;
      color: #202124;
      border: 1px solid #dadce0;
      border-bottom-left-radius: 4px;
    }
    .tool-badge {
      font-size: 11px;
      font-family: monospace;
      color: #5f6368;
      background: #eef0f2;
      padding: 2px 6px;
      border-radius: 4px;
      display: inline-block;
      margin-bottom: 6px;
    }
    .input-box {
      padding: 16px 24px;
      border-top: 1px solid #dadce0;
      display: flex;
      gap: 12px;
      background: white;
    }
    input {
      flex: 1;
      border: 1px solid #dadce0;
      border-radius: 24px;
      padding: 12px 20px;
      font-size: 14.5px;
      outline: none;
      font-family: inherit;
    }
    input:focus { border-color: #1a73e8; }
    button {
      background: #1a73e8;
      color: white;
      border: none;
      border-radius: 24px;
      padding: 12px 24px;
      font-weight: 500;
      cursor: pointer;
      font-family: inherit;
      transition: background 0.2s;
    }
    button:hover { background: #1557b0; }
    .hints {
      padding: 8px 24px 12px;
      background: white;
      font-size: 12px;
      color: #5f6368;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .chip {
      background: #f1f3f4;
      padding: 4px 10px;
      border-radius: 12px;
      cursor: pointer;
    }
    .chip:hover { background: #e8eaed; }
  </style>
</head>
<body>
  <div class="chat-container">
    <div class="chat-header">
      <div style="font-size: 24px;">🌈</div>
      <div>
        <h2 style="font-size: 18px; font-weight: 500;">Customer Experience — Rainbow Agent</h2>
        <div style="font-size: 12px; opacity: 0.9;">GCP-Native • Cloud Run • Firestore • Agent Platform</div>
      </div>
      <div class="badge">Live 🟢</div>
    </div>
    
    <div class="messages" id="msgs">
      <div class="msg agent">👋 Hi! I'm Rainbow, an AI Virtual Assistant. How can I help you today? You can ask about return policies, check order status, or initiate a return.</div>
    </div>

    <div class="hints">
      <span style="font-weight: 500;">Quick prompts:</span>
      <span class="chip" onclick="fillPrompt('What is your return policy?')">Return Policy</span>
      <span class="chip" onclick="fillPrompt('I want to return order BK-10001 (hasan2296@outlook.com)')">Return BK-10001</span>
      <span class="chip" onclick="fillPrompt('123456')">Enter OTP: 123456</span>
      <span class="chip" onclick="fillPrompt('Can you cancel order BK-10015?')">Cancel BK-10015</span>
    </div>

    <form class="input-box" onsubmit="sendMessage(event)">
      <input type="text" id="userInput" placeholder="Type a message..." autocomplete="off" autofocus />
      <button type="submit" id="sendBtn">Send</button>
    </form>
  </div>

  <script>
    const msgs = document.getElementById('msgs');
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');

    function fillPrompt(text) {
      input.value = text;
      input.focus();
    }

    async function sendMessage(e) {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;

      // Append user msg
      const userDiv = document.createElement('div');
      userDiv.className = 'msg user';
      userDiv.textContent = text;
      msgs.appendChild(userDiv);
      input.value = '';
      msgs.scrollTop = msgs.scrollHeight;

      // Loading indicator
      const loadDiv = document.createElement('div');
      loadDiv.className = 'msg agent';
      loadDiv.id = 'loading';
      loadDiv.textContent = 'Rainbow is thinking...';
      msgs.appendChild(loadDiv);
      msgs.scrollTop = msgs.scrollHeight;
      sendBtn.disabled = true;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        loadDiv.remove();

        const agentDiv = document.createElement('div');
        agentDiv.className = 'msg agent';

        if (data.tools && data.tools.length) {
          const tb = document.createElement('div');
          tb.className = 'tool-badge';
          tb.textContent = '⚙️ Executed: ' + data.tools.join(', ');
          agentDiv.appendChild(tb);
        }

        const textSpan = document.createElement('div');
        textSpan.textContent = data.reply || '(No response)';
        agentDiv.appendChild(textSpan);

        msgs.appendChild(agentDiv);
      } catch (err) {
        loadDiv.textContent = '❌ Error: ' + err.message;
      } finally {
        sendBtn.disabled = false;
        msgs.scrollTop = msgs.scrollHeight;
        input.focus();
      }
    }
  </script>
</body>
</html>
"""


class ChatHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode())
            user_message = req.get("message", "")

            token = get_token()
            session_id = get_or_create_session(token)

            payload = {
                "appName": "app",
                "userId": "hasan-rahman",
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": user_message}],
                },
            }

            url = f"{CLOUD_RUN_URL}/run"
            api_req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(api_req) as resp:
                    events = json.loads(resp.read().decode())

                reply_parts = []
                tools_used = []
                for ev in events:
                    content = ev.get("content", {})
                    parts = content.get("parts", [])
                    for p in parts:
                        if "functionCall" in p:
                            tools_used.append(p["functionCall"]["name"])
                        elif "text" in p and p["text"].strip():
                            reply_parts.append(p["text"].strip())

                reply_text = "\n\n".join(reply_parts)
                response_data = {
                    "reply": reply_text,
                    "tools": list(dict.fromkeys(tools_used)),
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), ChatHandler) as httpd:
        print(f"Customer Experience Web UI running at http://127.0.0.1:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
