# ExecPlan Standard for Modernization & Agent Development

This document defines the mandatory standard for Executive Plans (**ExecPlans**) in this repository, based on the [OpenAI Code Modernization Framework](https://developers.openai.com/cookbook/examples/codex/code_modernization).

An ExecPlan is a **living design and tracking document** that serves as the single source of truth for delivering bounded system changes, modernizations, or new customer support flows.

---

## When to Use an ExecPlan

Create or update an ExecPlan whenever:
1. Modernizing a legacy or prototype subsystem (e.g. migrating Sheets/Stytch/Chroma to GCP-native Firestore).
2. Implementing a new multi-turn customer support journey (e.g. order exchanges, subscription management).
3. Modifying core agent routing, guardrails, or tool schemas that require multi-turn parity evaluation.

---

## The 4 Core Artifacts

Every pilot flow or modernization initiative is governed by 4 dedicated documents:

1. **`pilot_execplan.md`**: The orchestrating living document (scope, progress, decision logs, acceptance).
2. **`pilot_overview.md`**: Inventory of existing programs, jobs, data flows, schemas, and human SOPs.
3. **`pilot_design.md`**: Target system architecture, module boundaries, database schemas, and OpenAPI specs.
4. **`pilot_validation.md`**: Parity test plan, golden eval datasets, edge cases, and side-by-side verification steps.

---

## Required ExecPlan Structure

Any `pilot_execplan.md` created in `docs/` must follow this skeleton:

```markdown
# ExecPlan: [Flow or Modernization Name]

## 1. Scope & Objective
- **Business Goal**: Plain-language description of what this change accomplishes.
- **In-Scope Components**: Exact tools, collections, and files touched.
- **Out-of-Scope**: Explicit boundaries of what is excluded.

## 2. Document References
- Overview & Inventory: [`docs/pilot_overview.md`](pilot_overview.md)
- Target Design & Spec: [`docs/pilot_design.md`](pilot_design.md)
- Validation & Parity: [`docs/pilot_validation.md`](pilot_validation.md)

## 3. Implementation Steps
- [ ] Phase 1: Pilot scoping and alignment
- [ ] Phase 2: Technical inventory & discovery report
- [ ] Phase 3: Target architecture, schemas, and test scaffolding
- [ ] Phase 4: Implementation, data seeding, and parity validation
- [ ] Phase 5: Production readiness & deployment notes

## 4. Progress & Milestones
- [x] Milestone completed description (commit or PR link)
- [ ] Upcoming task description

## 5. Decision Log
| Date | Decision | Rationale | Alternatives Considered |
|---|---|---|---|
| YYYY-MM-DD | Chosen approach | Why it was selected | Why other options were rejected |

## 6. Surprises & Discoveries
- Uncovered edge cases, unexpected API limits, or undocumented legacy behaviors encountered during implementation.

## 7. Acceptance Criteria & Validation Results
- Automated unit and integration test outputs (`pytest`).
- Evaluation benchmark scores (`agents-cli eval run`).
- Parity comparison results between legacy baseline and modern implementation.
```

---

## Agent Instructions for Maintaining ExecPlans

1. **Keep It Living**: Update `Progress`, `Decision Log`, and `Surprises & Discoveries` after completing each meaningful chunk of work.
2. **Never Stale**: If requirements change during implementation, update the ExecPlan first before modifying code.
3. **Parity First**: Always verify that the acceptance criteria and validation results are recorded before declaring a flow complete.
