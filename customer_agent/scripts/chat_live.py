#!/usr/bin/env python3
"""Interactive Live Terminal Chat with Customer Experience Agent on Cloud Run."""

import json
import subprocess
import sys
import urllib.request

CLOUD_RUN_URL = "https://rainbow-agent-642781268620.us-central1.run.app"


def get_gcloud_token() -> str:
    try:
        return (
            subprocess.check_output(
                ["gcloud", "auth", "print-identity-token"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception as e:
        print(f"Error getting gcloud identity token: {e}")
        sys.exit(1)


def api_post(endpoint: str, payload: dict | None = None, token: str = "") -> dict | list:
    url = f"{CLOUD_RUN_URL}{endpoint}"
    data = json.dumps(payload).encode() if payload is not None else b""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def main():
    print("=" * 65)
    print(" 📚 Welcome to Customer Experience — Live Cloud Run Agent")
    print(f" Connecting to: {CLOUD_RUN_URL}")
    print("=" * 65)

    token = get_gcloud_token()

    # Default customer identifier
    user_id = "hasan-rahman"
    print(f"\n[Session] Creating session for user '{user_id}'...")
    session = api_post(f"/apps/app/users/{user_id}/sessions", token=token)
    session_id = session.get("id")
    print(f"[Session] Active session ID: {session_id}")
    print("\nYou can now chat with the Assistant! Type 'exit' or 'quit' to end.\n")
    print("💡 Hints:")
    print("  • Ask about returns: 'I want to return order BK-10001 (hasan2296@outlook.com)'")
    print("  • Verification code: when prompted for OTP, enter '123456'")
    print("  • Ask about policy: 'What is your return policy?'")
    print("  • Ask about cancellation: 'Can you cancel order BK-10015?'")
    print("-" * 65)

    while True:
        try:
            user_input = input("\n👤 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat. Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        payload = {
            "appName": "app",
            "userId": user_id,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": user_input}],
            },
        }

        print("⏳ Assistant is thinking...", end="\r", flush=True)

        try:
            events = api_post("/run", payload, token=token)
            print(" " * 30, end="\r")  # clear line

            agent_spoke = False
            for ev in events:
                content = ev.get("content", {})
                parts = content.get("parts", [])
                for p in parts:
                    if "functionCall" in p:
                        fn = p["functionCall"]
                        print(f"   ⚙️  [Tool Call] {fn['name']}({json.dumps(fn.get('args', {}))})")
                    elif "functionResponse" in p:
                        fr = p["functionResponse"]
                        resp_str = json.dumps(fr.get("response", {}))
                        if len(resp_str) > 100:
                            resp_str = resp_str[:100] + "..."
                        print(f"   📥 [Tool Result] {fr['name']} -> {resp_str}")
                    elif "text" in p and p["text"].strip():
                        print(f"\n🤖 Assistant: {p['text'].strip()}")
                        agent_spoke = True

            if not agent_spoke:
                print("\n🤖 Assistant: (No text response received)")

        except Exception as e:
            print(f"\n❌ Error communicating with Cloud Run: {e}")


if __name__ == "__main__":
    main()
