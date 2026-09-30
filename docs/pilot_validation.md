# Parity & Validation Strategy: Firestore Modernization

## 1. Overview & Objectives

This document defines how we prove behavioral parity between the legacy demo (Google Sheets, Stytch, local ChromaDB) and the modern GCP-native implementation (Cloud Firestore, Firestore Vector Search, Firestore OTP, Cloud Logging).

It fulfills the **Phase 3 (Validation Plan)** requirement of the [OpenAI Code Modernization Framework](https://developers.openai.com/cookbook/examples/codex/code_modernization).

---

## 2. Parity Scenario Matrix

The test harness must exercise 12 critical behavioral scenarios across both unit and integration layers:

| ID | Scenario | Input Data | Expected Result | Parity Criterion |
| :--- | :--- | :--- | :--- | :--- |
| **SC-01** | **OTP Send & Verify** | `email: "hasan2296@outlook.com"`, correct OTP | Success message; `verified: True` | Matches Stytch OTP verification flow |
| **SC-02** | **OTP 2-Strike Lockout** | `email: "hasan2296@outlook.com"`, 2 consecutive invalid codes | 1st failure: `1 attempt remaining`<br>2nd failure: `Locked. Escalation required.` | Enforces code-level lockout identically |
| **SC-03** | **OTP Expiration** | Expired code (`now > expires_at`) | Rejection: `Code expired, please request a new one.` | Security TTL parity |
| **SC-04** | **Order Lookup (Owner)** | `order: "BK-10001"`, `verified_email: "hasan2296@outlook.com"` | Returns full order dict (Delivered status, item, address) | 100% field parity with Sheets `Orders` row |
| **SC-05** | **Order Lookup (Non-Owner)** | `order: "BK-10001"`, `verified_email: "attacker@example.com"` | Strict refusal: `Order does not belong to verified account.` | Deterministic code-level security |
| **SC-06** | **Customer Account Lookup** | `verified_email: "hasan2296@outlook.com"` | Returns Hasan Rahman's name, phone, home address | No external email argument accepted |
| **SC-07** | **Eligible Return Initiation** | `order: "BK-10001"`, `reason: "Changed mind"` | Success confirmation; updates `return_status: "Requested"` | Atomic mutation matching Sheets row update |
| **SC-08** | **Ineligible Return: Past 30 Days** | Order placed 45 days ago | Refusal: `Return window (30 days) has expired.` | Calendar calculation parity |
| **SC-09** | **Ineligible Return: Final Sale** | Order category: `Clearance` or `Rare/Collectible` | Refusal: `Final-sale items are not eligible for return.` | Policy rule parity |
| **SC-10** | **Pre-Shipment Cancellation** | Order in `Processing` status | Success; `shipping_status: "Cancelled"` | Atomic mutation matching Sheets behavior |
| **SC-11** | **Post-Shipment Cancellation** | Order in `Shipped` or `Delivered` status | Refusal: `Order has already shipped; use return flow.` | Workflow routing parity |
| **SC-12** | **Vector Search Policy Retrieval** | Query: "How long does standard shipping take?" | Retrieves "5–7 business days" domestic shipping chunk | Cosine similarity parity with ChromaDB |

---

## 3. Test Scaffolding & Execution

### 3.1 Automated Parity Suite (`tests/integration/test_firestore_parity.py`)
A comprehensive pytest suite verifying each tool in `customer_agent/app/gcp_tools.py` directly against the Firestore client layer:
```bash
cd customer_agent && uv run pytest tests/integration/test_firestore_parity.py -v
```

### 3.2 ADK Multi-Turn Evaluation Suite
Running the full multi-turn conversational agent against the golden datasets:
```bash
cd customer_agent
agents-cli eval run --dataset tests/eval/datasets/single-turn.json --config tests/eval/eval_config_single_turn.yaml
agents-cli eval run --dataset tests/eval/datasets/multi-turn.json --config tests/eval/eval_config_multi_turn.yaml
```

### 3.3 Acceptance Thresholds
- **Unit & Integration Tests**: 100% pass rate (`12/12` scenarios).
- **Single-Turn Evaluation**: Quality score $\ge 4.5/5.0$; zero safety regressions.
- **Multi-Turn Evaluation**: `task_success` $\ge 90\%$; `tool_use_quality` $\ge 90\%$.
