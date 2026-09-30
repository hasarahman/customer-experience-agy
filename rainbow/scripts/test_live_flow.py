#!/usr/bin/env python3
"""Automated 5-turn test harness for the Customer Experience Agent on Cloud Run."""

import json
import subprocess
import sys
import urllib.request

CLOUD_RUN_URL = "https://rainbow-agent-642781268620.us-central1.run.app"


def get_token():
    return (
        subprocess.check_output(
            ["gcloud", "auth", "print-identity-token"], stderr=subprocess.DEVNULL
        )
        .decode()
        .strip()
    )


def create_session(token, user_id):
    url = f"{CLOUD_RUN_URL}/apps/app/users/{user_id}/sessions"
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
        return data["id"]


def send_turn(token, user_id, session_id, user_text):
    payload = {
        "appName": "app",
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {
            "role": "user",
            "parts": [{"text": user_text}],
        },
    }
    url = f"{CLOUD_RUN_URL}/run"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
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
                clean_text = p["text"].strip()
                if clean_text not in reply_parts:
                    reply_parts.append(clean_text)

    reply_text = "\n\n".join(reply_parts)
    return reply_text, list(dict.fromkeys(tools_used))


def run_tests():
    print("=" * 70)
    print("🚀 CUSTOMER EXPERIENCE AGENT: PRE-RECORDING LIVE TEST HARNESS")
    print("=" * 70)

    token = get_token()
    user_id = f"eval-user-{id(object())}"
    session_id = create_session(token, user_id)
    print(f"✅ Created Live Session on Cloud Run: {session_id} for {user_id}\n")

    turns = [
        {
            "turn": 1,
            "user": "Hi",
            "expect_tool": None,
            "validate": lambda reply, tools: "Rainbow" in reply and "help" in reply.lower(),
            "desc": "Rainbow greeting returned",
        },
        {
            "turn": 2,
            "user": "I haven't received my order yet, can you check on my order? I lost my order number.",
            "expect_tool": None,
            "validate": lambda reply, tools: any(k in reply.lower() for k in ["email", "reverse lookup"]),
            "desc": "Offers email reverse lookup for lost order number",
        },
        {
            "turn": 3,
            "user": "hasan2296@outlook.com",
            "expect_tool": "send_auth_code",
            "validate": lambda reply, tools: (
                "send_auth_code" in tools
                and any(k in reply.lower() for k in ["code", "verification", "sent"])
            ),
            "desc": "Executes send_auth_code to verify identity before revealing orders",
        },
        {
            "turn": 4,
            "user": "123456",
            "expect_tool": "verify_auth_code",
            "validate": lambda reply, tools: (
                "verify_auth_code" in tools
                and "find_orders_by_email" in tools
                and ("Project Hail Mary" in reply or "Midnight Library" in reply)
            ),
            "desc": "Executes verify_auth_code & find_orders_by_email, listing customer orders",
        },
        {
            "turn": 5,
            "user": "Project Hail Mary",
            "expect_tool": "lookup_order",
            "validate": lambda reply, tools: (
                "lookup_order" in tools
                and ("processing" in reply.lower() or "preparing" in reply.lower())
            ),
            "desc": "Executes lookup_order & reports 'Processing' status",
        },
        {
            "turn": 6,
            "user": "whats your return window?",
            "expect_tool": "search_policy_kb",
            "validate": lambda reply, tools: (
                "search_policy_kb" in tools
                and "30" in reply
            ),
            "desc": "Executes search_policy_kb & reports 30-day return policy",
        },
    ]

    all_passed = True
    for t in turns:
        print(f"--- TURN {t['turn']} ---")
        print(f"👤 USER: {t['user']}")
        reply, tools = send_turn(token, user_id, session_id, t["user"])
        print(f"⚙️  TOOLS USED: {tools if tools else 'None'}")
        print(f"🤖 RAINBOW:\n{reply}\n")

        # Check for duplication bug
        paragraphs = [p.strip() for p in reply.split("\n\n") if p.strip()]
        if len(paragraphs) != len(set(paragraphs)):
            print(f"❌ BUG DETECTED: Duplicate paragraphs found in reply!")
            all_passed = False
            continue

        passed = t["validate"](reply, tools)
        if passed:
            print(f"✅ Turn {t['turn']} PASSED: {t['desc']}\n")
        else:
            print(f"❌ Turn {t['turn']} FAILED validation: {t['desc']}\n")
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("🎉 ALL 5/5 TURNS PASSED! System is ready for automated recording.")
        print("=" * 70)
        return 0
    else:
        print("⚠️ SOME TURNS FAILED. Check responses above.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
