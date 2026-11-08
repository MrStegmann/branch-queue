# Tasks: Design Notes (`DESIGN.md`)

**Input**: Design documents from `/specs/002-design-notes/`
**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required for user stories), [research.md](research.md), [data-model.md](data-model.md), [contracts/design-document-contract.md](contracts/design-document-contract.md)
**Tests**: Automated document assertion tests verifying Spanish language compliance, Big-O algorithmic complexity claims, race condition analysis, and atomic state mutation guarantees.
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Exact file paths are included in all task descriptions

## Path Conventions

- Documentation deliverable: `./DESIGN.md` at repository root
- Domain codebase: `src/models/`, `src/services/`
- Test suite: `tests/unit/test_design_notes.py`
- Spec artifacts: `specs/002-design-notes/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and test framework scaffolding for design document assertions

- [X] T001 Create validation test skeleton in tests/unit/test_design_notes.py for automated document verification
- [X] T002 [P] Initialize the root document structure in DESIGN.md with title and main outline per specs/002-design-notes/contracts/design-document-contract.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish document contract structure and base assertions that all user stories depend upon

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Add document contract validation test suite in tests/unit/test_design_notes.py covering required markdown headers and structure
- [X] T004 [P] Establish Spanish terminology and architectural reference definitions in DESIGN.md (BranchQueueManager, ServiceType, and Constitution principles)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Rationale for Per-Service Queue Efficiency (Priority: P1) 🎯 MVP

**Goal**: Explain why dedicated per-service FIFO queues make `call_next` asymptotically and operationally superior ($O(1)$ direct access) compared to a single shared queue ($O(N)$ linear scanning and item removal penalty).

**Independent Test**: Run automated assertions in `tests/unit/test_design_notes.py` verifying $O(1)$ and $O(N)$ algorithmic complexity explanations, filtering overhead contrast, and inspect Section 1 of `DESIGN.md`.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T005 [P] [US1] Add automated test for O(1) vs O(N) efficiency assertions in tests/unit/test_design_notes.py

### Implementation for User Story 1

- [X] T006 [US1] Author Section 1.1 & 1.2 on data modeling and O(1) vs O(N) time complexity comparison in DESIGN.md
- [X] T007 [US1] Author Section 1.3 & 1.4 on element removal shifting overhead and lock contention partitioning in DESIGN.md

**Checkpoint**: User Story 1 complete. `DESIGN.md` clearly explains per-service queue efficiency with $O(1)$ vs $O(N)$ complexity analysis.

---

## Phase 4: User Story 2 - Concurrency Hazards and State Mutation Ordering (Priority: P1)

**Goal**: Document simultaneous `call_next` execution by two agents handling the same service type, detail the Check-Then-Act (TOCTOU) race condition, and identify that atomic extraction (`popleft` in critical section) is the mandatory first state mutation.

**Independent Test**: Run automated assertions in `tests/unit/test_design_notes.py` verifying race condition explanations, state mutation ordering identification, and edge cases (single client, empty queue, agent crash).

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US2] Add automated test for concurrency and mutation ordering assertions in tests/unit/test_design_notes.py

### Implementation for User Story 2

- [X] T009 [US2] Author Section 2 on dual agent collision and Check-Then-Act (TOCTOU) race condition with timeline diagrams in DESIGN.md
- [X] T010 [US2] Author Section 3.1 & 3.2 answering the central state mutation question and detailing atomic popleft extraction in DESIGN.md
- [X] T011 [US2] Author Section 3.3 covering edge cases (single client, empty queue, and agent crash handling) in DESIGN.md

**Checkpoint**: User Stories 1 AND 2 are complete. Both the efficiency rationale and concurrency/state mutation analyses are fully articulated.

---

## Phase 5: User Story 3 - Full Spanish Language and Document Standards Compliance (Priority: P2)

**Goal**: Ensure 100% Spanish language compliance across all prose and headings in `DESIGN.md`, verify markdown structure, and align with the Branch Queue Constitution.

**Independent Test**: Run language and structure checks in `tests/unit/test_design_notes.py` to confirm zero English narrative sentences and complete alignment with Constitution principles.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US3] Add automated test for full Spanish prose compliance and forbidden English phrases in tests/unit/test_design_notes.py

### Implementation for User Story 3

- [X] T013 [US3] Author Section 4 detailing alignment with Branch Queue Constitution Principles II, IV, and V in DESIGN.md
- [X] T014 [US3] Review and standardize Spanish grammar, diacritics, and technical formatting across all sections in DESIGN.md

**Checkpoint**: All user stories complete. The document is fully in Spanish, structurally sound, and aligned with project constitution.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, quality validation, and end-to-end checks

- [X] T015 [P] Run full test suite with pytest tests/unit/test_design_notes.py
- [X] T016 Execute end-to-end quickstart validation script from specs/002-design-notes/quickstart.md
- [X] T017 [P] Verify markdown formatting and table rendering in DESIGN.md against specs/002-design-notes/contracts/design-document-contract.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories.
- **User Stories (Phases 3-5)**: All depend on Foundational (Phase 2) completion.
  - User Story 1 (P1) and User Story 2 (P1) address the core architectural questions.
  - User Story 3 (P2) completes Spanish language verification and Constitution alignment.
- **Polish (Phase 6)**: Depends on all user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on US2 or US3.
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Expands on dispatch concurrency independently of US1 efficiency prose.
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Validates and unifies the complete document in Spanish.

### Within Each User Story

- Tests MUST be added first and fail before corresponding implementation.
- Section outlines before detailed narratives.
- Core answers and diagrams before edge cases.
- Each story is independently testable via unit assertions.

### Parallel Opportunities

- Phase 1: T001 and T002 can run in parallel.
- Phase 2: T003 and T004 can run in parallel.
- After Phase 2: User Story 1 and User Story 2 test tasks (T005, T008) can run in parallel.
- Phase 6: T015 and T017 can run in parallel.

---

## Parallel Execution Examples

### Parallel Example: User Story 1
```bash
# Launch test and implementation tasks:
Task: "T005 [P] [US1] Add automated test for O(1) vs O(N) efficiency assertions in tests/unit/test_design_notes.py"
```

### Parallel Example: User Story 2
```bash
# Launch test task for User Story 2:
Task: "T008 [P] [US2] Add automated test for concurrency and mutation ordering assertions in tests/unit/test_design_notes.py"
```

### Parallel Example: User Story 3
```bash
# Launch test task for User Story 3:
Task: "T012 [P] [US3] Add automated test for full Spanish prose compliance and forbidden English phrases in tests/unit/test_design_notes.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (`tests/unit/test_design_notes.py` skeleton, `DESIGN.md` outline)
2. Complete Phase 2: Foundational (Document headers, structural contract tests)
3. Complete Phase 3: User Story 1 (Algorithmic efficiency: $O(1)$ vs $O(N)$ analysis)
4. **STOP and VALIDATE**: Test User Story 1 independently via pytest and visual review.
5. Deployable MVP increment delivering the efficiency rationale.

### Incremental Delivery

1. Setup + Foundational → Document structure ready.
2. User Story 1 → Efficiency rationale documented ($O(1)$ vs $O(N)$) → MVP!
3. User Story 2 → Concurrency and state mutation ordering documented → Core questions answered!
4. User Story 3 → Full Spanish compliance, grammar polish, and Constitution alignment → Ready for review!
5. Phase 6: Polish → End-to-end quickstart script and full pytest test suite passing.

---

## Notes

- All tasks strictly adhere to the checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`.
- The [Story] labels ([US1], [US2], [US3]) are present only on user story tasks.
- Exactly 17 granular, actionable tasks defined.
- File paths point to real, tangible project files (`DESIGN.md`, `tests/unit/test_design_notes.py`, `specs/002-design-notes/quickstart.md`, `specs/002-design-notes/contracts/design-document-contract.md`).

