# ExecPlan: GCP-Native Firestore Modernization (Rainbow Agent)

## 1. Scope & Objective
- **Business Goal**: Modernize the Customer Experience Agent (`Rainbow`) from prototype backing services (Google Sheets, Stytch, local ChromaDB, local log files) to an enterprise-grade, **100% GCP-Native Firestore architecture** in project **`has-demo-50091`** (region `us-central1`).
- **In-Scope Components**:
  - `rainbow/app/tools.py` $\rightarrow$ Replaced/Modernized with `rainbow/app/gcp_tools.py` (Firestore data store, Firestore Vector Search, Firestore-backed OTP, Cloud Logging).
  - `rainbow/scripts/seed_firestore.py` $\rightarrow$ Populate initial `customers` and `orders` data.
  - `rainbow/scripts/index_knowledge_base.py` $\rightarrow$ Chunk and embed `data/customer_experience_knowledge_base.md` using Agent Platform `text-embedding-004` into Firestore `policies`.
  - `rainbow/app/agent.py` $\rightarrow$ Wire modernized GCP tools into `root_agent`.
  - `rainbow/tests/integration/test_firestore_parity.py` $\rightarrow$ Deterministic parity test suite.
  - `rainbow/tests/eval/` $\rightarrow$ Golden single-turn and multi-turn ADK evaluation runs.
- **Out-of-Scope**:
  - Rewriting the ADK core agent loop or changing the underlying Gemini model (`gemini-3.5-flash-lite`).
  - Cloud infrastructure provisioning beyond the required Firestore collections and IAM permissions.

---

## 2. Document References
- Overview & Inventory: [`docs/pilot_overview.md`](pilot_overview.md)
- Target Design & Spec: [`docs/pilot_design.md`](pilot_design.md)
- Validation & Parity: [`docs/pilot_validation.md`](pilot_validation.md)
- SOP & Business Rules: [`docs/SOP.md`](SOP.md)

---

## 3. Implementation Steps
- [x] **Phase 0: Governance & Contract Setup**
  - Delete `rainbow/CLAUDE.md` and clean up manifest.
  - Create `.agent/AGENTS.md` and `.agent/PLANS.md`.
- [x] **Phase 1: Pilot Scoping & ExecPlan Generation**
  - Create `docs/pilot_execplan.md` targeting project `has-demo-50091`.
- [x] **Phase 2: Technical Inventory & Discovery Report**
  - Create `docs/pilot_overview.md` documenting end-to-end flows, schemas, and guardrails.
- [x] **Phase 3: Target Architecture, Schemas & Test Scaffolding**
  - Draft `docs/pilot_design.md` detailing Firestore transactional logic and vector indexes.
  - Draft `docs/pilot_validation.md` defining parity criteria and test harness.
  - Scaffold `rainbow/tests/integration/test_firestore_parity.py`.
- [x] **Phase 4: Implementation, Data Seeding & Parity Validation**
  - Implement `rainbow/scripts/seed_firestore.py` and `rainbow/scripts/index_knowledge_base.py`.
  - Implement `rainbow/app/gcp_tools.py` with mock/emulator support for offline execution.
  - Update `rainbow/app/agent.py` to use GCP tools.
  - Execute automated tests (`pytest` / `unittest`) verifying all 12 parity scenarios.
- [x] **Phase 5: Production Readiness & Reusable Templates**
  - Generate `docs/template_modernization_execplan.md`.
  - Document Cloud Run deployment and IAM configuration in `docs/deployment_guide.md`.
  - Execute end-to-end integration test (`tests/integration/test_e2e_simulation.py`).

---

## 4. Progress & Milestones
- **2026-09-29**: Phase 0 completed. All Claude references permanently purged; `.agent/AGENTS.md` and `.agent/PLANS.md` established.
- **2026-09-29**: Phase 1 & 2 completed. Codebase anatomy and system inventory synthesized in `docs/pilot_overview.md`; `docs/pilot_execplan.md` initialized.
- **2026-09-29**: Phase 3 completed. Target GCP architecture specified in `docs/pilot_design.md`; parity validation matrix defined in `docs/pilot_validation.md`.
- **2026-09-29**: Phase 4 completed. Implemented `gcp_client.py`, `gcp_tools.py`, `seed_firestore.py`, and `index_knowledge_base.py`. Automated parity suite passed 100% (12/12 scenarios).
- **2026-09-29**: Phase 5 completed. Reusable template created (`docs/template_modernization_execplan.md`), Cloud Run deployment guide published (`docs/deployment_guide.md`), and End-to-End customer journey test passed 100%.

---

## 5. Decision Log
| Date | Decision | Rationale | Alternatives Considered |
|---|---|---|---|
| 2026-09-29 | Target GCP Project: `has-demo-50091` | Designated project for demo modernization | Local mock only |
| 2026-09-29 | Cloud Firestore for Data Store | Serverless NoSQL, ACID transactions, native IAM ADC authentication | Cloud SQL (Postgres), BigQuery |
| 2026-09-29 | Firestore Vector Search with `text-embedding-004` | Consolidates all data and vectors in Firestore; no external vector database needed | Agent Platform Search (Agent Builder), ChromaDB |
| 2026-09-29 | Firestore-Backed OTP Service | Native GCP solution with atomic transaction-enforced 2-strike lockout and TTL | Cloud Identity Platform (GCIP), Stytch |
| 2026-09-29 | Cloud Logging & `escalations` collection | Centralized audit trail for human agents and support teams | Flat log file append |
| 2026-09-29 | Zero Claude References | User requirement for clean codebase governance | Keeping `CLAUDE.md` |

---

## 6. Surprises & Discoveries
1. **Desktop OAuth Fragility**: The legacy Google Sheets integration relied on an interactive desktop OAuth token file (`google_token.json`) that expires and cannot run in automated CI/CD or serverless runtimes. Moving to Firestore with Application Default Credentials (ADC) resolves this fundamentally.
2. **Hardcoded Author Paths**: The original `tools.py` and `build_index.py` hardcoded paths like `/Users/hasanrahman/dcg/...`. The new GCP tools will be decoupled from filesystem paths and configured purely via environment variables.
3. **Deterministic Guardrails**: The original codebase cleverly enforced critical guardrails in Python (order ownership, 30-day window, OTP lockout). We must preserve 100% behavioral parity for these rules in Firestore transactions.

---

## 7. Acceptance Criteria & Validation Results
- [x] `seed_firestore.py` successfully written for customers and orders.
- [x] `index_knowledge_base.py` successfully written for policy chunks and Agent Platform embeddings.
- [x] `lookup_order` enforces `verified_email` ownership and returns order details.
- [x] `lookup_customer` returns only the verified customer's profile.
- [x] `initiate_return` enforces 30-day window and final-sale category exclusions.
- [x] `cancel_order` only permits cancellations for orders in `Processing` status.
- [x] `verify_auth_code` locks out after 2 consecutive failed attempts.
- [x] `search_policy_kb` retrieves matching policy chunks via semantic/vector search.
- [x] Automated test suite `tests/integration/test_firestore_parity.py` passes 100% (12/12 scenarios).
- [x] End-to-End customer journey simulation test `tests/integration/test_e2e_simulation.py` passes 100%.
- [x] Production Cloud Run deployment guide and factory template completed.
