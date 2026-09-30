# Modernization ExecPlan Template: [Flow Name]

> **Instructions**: Use this template to onboard and modernize any new customer support journey (e.g. order exchanges, subscription changes, lost package claims) following the [OpenAI Code Modernization Framework](https://developers.openai.com/cookbook/examples/codex/code_modernization).

---

# ExecPlan: [Insert Flow Name]

## 1. Scope & Objective
- **Business Goal**: Plain-language description of what this change accomplishes for Customer Experience customers.
- **In-Scope Components**:
  - `customer_agent/app/gcp_tools.py` $\rightarrow$ Tools to add or modify.
  - Firestore collections affected (`customers`, `orders`, `otps`, `policies`, `escalations`, or new collection).
  - Prompts in `customer_agent/app/agent.py`.
- **Out-of-Scope**: Explicit boundaries of what is excluded.

---

## 2. Document References
- Overview & Inventory: [`docs/[flow]_overview.md`]([flow]_overview.md)
- Target Design & Spec: [`docs/[flow]_design.md`]([flow]_design.md)
- Validation & Parity: [`docs/[flow]_validation.md`]([flow]_validation.md)
- Human SOP: [`docs/SOP.md`](SOP.md)

---

## 3. Implementation Steps
- [ ] **Phase 1: Scoping & Alignment**
  - Define bounded pilot flow and success criteria.
  - Initialize this ExecPlan.
- [ ] **Phase 2: Technical Inventory & Discovery**
  - Document existing manual SOP and data requirements in `docs/[flow]_overview.md`.
- [ ] **Phase 3: Target Architecture, Schemas & Validation Spec**
  - Define Firestore document schemas and atomic transaction logic in `docs/[flow]_design.md`.
  - Create parity test scenarios matrix in `docs/[flow]_validation.md`.
  - Scaffold tests in `customer_agent/tests/integration/test_[flow]_parity.py`.
- [ ] **Phase 4: Implementation & Validation Loop**
  - Implement business tools in `customer_agent/app/gcp_tools.py`.
  - Register tools in `customer_agent/app/agent.py`.
  - Run parity test suite (`pytest`) and verify 100% pass rate.
  - Run ADK eval suite (`agents-cli eval run`).
- [ ] **Phase 5: Production Readiness & Release**
  - Update decision log, surprises & discoveries, and acceptance checklist.
  - Verify Cloud Run deployment.

---

## 4. Progress & Milestones
- **YYYY-MM-DD**: Milestone description (commit or PR link).

---

## 5. Decision Log
| Date | Decision | Rationale | Alternatives Considered |
|---|---|---|---|
| YYYY-MM-DD | Chosen design/tool pattern | Why chosen | Other options rejected |

---

## 6. Surprises & Discoveries
- Note unexpected edge cases, data inconsistencies, or policy ambiguities discovered during implementation.

---

## 7. Acceptance Criteria & Validation Results
- [ ] Deterministic guardrails verified (ownership, category exclusions, time windows).
- [ ] Firestore atomic transactions validated under concurrent calls.
- [ ] Integration tests pass 100%.
- [ ] ADK eval benchmark scores meet quality thresholds ($\ge 90\%$).
