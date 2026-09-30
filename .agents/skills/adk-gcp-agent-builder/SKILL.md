---
name: adk-gcp-agent-builder
description: >-
  Build, test, and deploy production-grade GCP-native AI agents using Google ADK,
  agents-cli, Cloud Firestore for transactional data/state, Agent Platform for embeddings
  and RAG vector search, and Cloud Run for serverless deployment with IAM-authenticated
  local proxying.
---

# ADK GCP Agent Builder

A complete, production-grade guide and operational framework for architecting, testing, and deploying Google Cloud Platform (GCP)-native AI agents with the Google Agent Development Kit (ADK) and Google Cloud services.

---

## Overview

This skill guides you through the full lifecycle of building autonomous enterprise agents:
1. **Agent Architecture & Prompt Engineering**: Multi-turn dialogue, strict verification guardrails, and ADK agent/app definitions.
2. **Operational Datastore with Cloud Firestore**: Schema design for customers, orders, OTP authentication state, and policy chunks.
3. **Agent Platform Embeddings & RAG**: Vectorizing markdown domain knowledge with `text-embedding-004` (768 dimensions) and cosine similarity retrieval.
4. **Stateful Security Tools**: OTP identity verification with rate-limiting and a 2-attempt lockout enforced in Firestore before granting access to sensitive data.
5. **Deterministic Integration Testing**: In-memory mock fallbacks and live Firestore parity test suites with automated state cleanup.
6. **Cloud Run Containerization & Deployment**: Packaging with `uv`, building with Artifact Registry, and deploying to Cloud Run.
7. **Local Proxy & Interactive Testing**: Zero-dependency web chat UI with automatic `gcloud auth` IAM token injection.

---

## Dependencies

This skill integrates with and references the following ADK skills:
- **`google-agents-cli-scaffold`**: For initializing project layouts (`agents-cli scaffold create`).
- **`google-agents-cli-adk-code`**: For ADK Python patterns (`Agent`, `App`, `Gemini`, tool signatures).
- **`google-agents-cli-deploy`**: For service accounts, Cloud Run configurations, and IAM permissions.
- **`google-agents-cli-workflow`**: For the high-level ADK lifecycle (scaffold -> build -> eval -> deploy).

---

## Quick Start

```bash
# 1. Initialize project directory structure
agents-cli scaffold create --template default --output my-agent

# 2. Configure GCP Manager & Firestore Client
# Copy template from templates/gcp_client.py into my-agent/app/gcp_client.py

# 3. Seed Firestore with operational data
python my-agent/scripts/seed_firestore.py

# 4. Index Knowledge Base into Firestore with Agent Platform Embeddings
python my-agent/scripts/index_knowledge_base.py data/knowledge_base.md

# 5. Run Parity Test Suite
pytest my-agent/tests/integration/test_firestore_parity.py

# 6. Deploy to Cloud Run via Artifact Registry
gcloud run deploy my-agent-service --source my-agent --project <PROJECT_ID> --region us-central1

# 7. Start Local Test Proxy & Web UI
gcloud run services proxy my-agent-service --port 8080 &
python my-agent/scripts/web_chat.py
```

---

## End-to-End Workflow

### Step 1: ADK Agent Architecture & App Setup

Create your agent definition in `app/agent.py`:

```python
import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from app.gcp_tools import (
    lookup_customer,
    lookup_order,
    initiate_return,
    cancel_order,
    send_auth_code,
    verify_auth_code,
    search_policy_kb,
    escalate_to_human,
)

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

INSTRUCTION = """You are an AI Virtual Assistant for Customer Experience at an online bookstore.

You help with four things: order status inquiries, return/refund requests, order cancellation
(before shipping), and general questions (shipping, policies, password reset).

## Identity verification (required before touching order or account data)
Before looking up orders or initiating returns:
1. Ask for their account email.
2. Call send_auth_code with that email.
3. Ask for the 6-digit code.
4. Call verify_auth_code with the email and code.
5. Only proceed with customer/order tools once verified.
"""

agent = Agent(
    name="customer_agent",
    model=Gemini(model=MODEL),
    instruction=INSTRUCTION,
    tools=[
        lookup_customer, lookup_order, initiate_return, cancel_order,
        send_auth_code, verify_auth_code, search_policy_kb, escalate_to_human,
    ],
)

app = App(name="app", agent=agent)
```

### Step 2: GCP Client Singleton & Mock Fallback

Use the reusable `GCPManager` pattern in `app/gcp_client.py` (see [templates/gcp_client.py](templates/gcp_client.py)):
- Connects to live Firestore when `GOOGLE_CLOUD_PROJECT` is set.
- Automatically falls back to an in-memory dictionary mock (`MockFirestoreClient`) for offline/local unit testing.
- Connects to Agent Platform `text-embedding-004` for vector embeddings.

### Step 3: Agent Platform Vector RAG Grounding

1. Split domain documents by markdown headers (`## `) to preserve semantic coherence.
2. Generate 768-dimensional embeddings using Agent Platform `text-embedding-004`.
3. Store chunk text and embedding vectors into Firestore collection `policies`.
4. At query time, embed the user's question, compute cosine similarity, and retrieve the top matching chunks for agent grounding (see [references/agent_platform_rag_patterns.md](references/agent_platform_rag_patterns.md)).

### Step 4: Stateful Tools & Security Lockout

Implement stateful tools in `app/gcp_tools.py`:
- **`send_auth_code(email)`**: Generates a 6-digit code, stores it in `otps/{email}` with `attempts: 0`, `locked: false`.
- **`verify_auth_code(email, code)`**: Enforces a strict 2-attempt limit. On the second failure, flags `locked: true` and directs the agent to call `escalate_to_human`.
- **`lookup_order(order_id, verified_email)`**: Requires email match with the order document and verified OTP status.
- **`initiate_return(order_id, verified_email, reason)`**: Validates 30-day window, non-final sale status, and updates `return_status: "Requested"`.

### Step 5: Seeding & Integration Testing

1. **Seed Firestore**: Run `seed_firestore.py` (see [templates/seed_script.py](templates/seed_script.py)) to populate sample customers and orders.
2. **Test Parity**: Validate both mock and live Firestore execution:
   - Reset mutable documents (e.g. `return_status: None`) in `setUp()`.
   - Use dynamic unique emails for lockout tests (`f"lockout.{time.time()}@test.com"`) to prevent locking shared test accounts.
3. **E2E Customer Simulation**: Run multi-turn conversation simulations verifying that the agent navigates greeting -> email -> OTP prompt -> verification -> order resolution.

### Step 6: Cloud Run Containerization & Deployment

1. Package using multi-stage `uv` in `Dockerfile` (see [references/cloud_run_deploy_patterns.md](references/cloud_run_deploy_patterns.md)).
2. Deploy directly with `gcloud run deploy`:
   ```bash
   gcloud run deploy <service-name> \
     --source . \
     --project <project-id> \
     --region us-central1 \
     --set-env-vars GOOGLE_CLOUD_PROJECT=<project-id>,GOOGLE_CLOUD_LOCATION=us-central1 \
     --quiet
   ```
   *Note: Cloud Build automatically routes source deploys to Google Artifact Registry (`us-central1-docker.pkg.dev`), bypassing deprecated `gcr.io` repos.*

### Step 7: Local Authenticated Testing & UI

1. Run `gcloud run services proxy <service-name> --port 8080` in the background to handle IAM authentication automatically.
2. Launch `templates/web_chat_template.py` on port 8085. It generates local `gcloud auth print-identity-token` headers and provides a live browser chat UI at `http://127.0.0.1:8085`.

---

## Common Mistakes & Troubleshooting

### 1. `denied: gcr.io repo does not exist`
- **Cause**: Modern GCP projects do not enable legacy Google Container Registry (`gcr.io`).
- **Fix**: Use `gcloud run deploy --source` or push directly to Google Artifact Registry:
  `us-central1-docker.pkg.dev/<project-id>/<repo-name>/<image>`.

### 2. Integration Test Cascading Failures
- **Cause**: Tests mutating live Firestore documents (e.g. order returns or lockout flags) persist across test runs.
- **Fix**: Explicitly reset document state in `setUp()`, or use timestamp-isolated IDs.

### 3. Agent Tool Call Argument Hallucination
- **Cause**: Missing or vague type annotations in tool signatures.
- **Fix**: Use strict Python type hints (`order_id: str, verified_email: str`) and detailed Google-style docstrings describing each parameter.

---

## Reference & Template Files

- [Firestore State Patterns](references/firestore_patterns.md)
- [Agent Platform RAG & Vector Search](references/agent_platform_rag_patterns.md)
- [Cloud Run Deployment Patterns](references/cloud_run_deploy_patterns.md)
- [GCP Manager Client Template](templates/gcp_client.py)
- [Firestore Seeding Template](templates/seed_script.py)
- [Knowledge Base Vector Indexer](templates/index_kb_script.py)
- [Web Chat UI Server](templates/web_chat_template.py)
