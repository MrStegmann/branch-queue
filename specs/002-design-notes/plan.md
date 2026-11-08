# Implementation Plan: Design Notes (`DESIGN.md`)

**Branch**: `002-design-notes` | **Date**: 2026-11-08 | **Spec**: [specs/002-design-notes/spec.md](spec.md)

**Input**: Feature specification from `/specs/002-design-notes/spec.md`

## Summary

This feature delivers a comprehensive architectural design document (`DESIGN.md`) in the repository root written entirely in Spanish. The document explains why using dedicated, isolated FIFO queues for each service type (`deposit`, `withdrawal`, `account_management`) makes `call_next` asymptotically and operationally superior ($O(1)$ direct access) compared to a single shared queue ($O(N)$ linear scanning and array element shifting). Furthermore, it provides an in-depth concurrency analysis of two agents attempting to invoke `call_next` simultaneously for the same service type, diagnosing the "Check-Then-Act" (TOCTOU) race condition and definitively establishing that the atomic extraction/dequeuing of the ticket from the waiting structure (`popleft` under mutual exclusion) is the mandatory first state mutation required to prevent duplicate customer dispatch.

## Technical Context

**Language/Version**: Markdown (CommonMark / GFM) for `DESIGN.md`. Python 3.11+ / 3.14 for code references and validation verification scripts.  
**Primary Dependencies**: None (Standard Library for Python validation scripts, standard GitHub Markdown rendering).  
**Storage**: File system artifact at project root (`./DESIGN.md`).  
**Testing**: Automated markdown assertions script verifying Spanish linguistic compliance, presence of $O(1)$ and $O(N)$ algorithmic complexity arguments, race condition analysis, and atomic extraction state mutation designation.  
**Target Platform**: Universal / Cross-platform (Markdown document readable across Git repositories, text editors, and GitHub web preview).  
**Project Type**: Documentation / Architectural Decision & Design Specification.  
**Performance Goals**: N/A for static documentation. Documented dispatch mechanism guarantees $O(1)$ retrieval time complexity for `call_next`.  
**Constraints**: 100% Spanish language for all narrative, explanations, and headings. Standard code symbols and complexity notations (`call_next`, `DESIGN.md`, `O(1)`, `O(N)`, `popleft`, `WAITING`, `SERVING`) preserved verbatim in backticks.  
**Scale/Scope**: 1 root markdown file (`DESIGN.md`), ~150-300 lines of rigorous technical analysis.  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Compliance Status | Analysis & Verification |
| :--- | :--- | :--- |
| **I. Deterministic Sequential Ticket Issuance** | **PASS** | `DESIGN.md` reinforces monotonic and gapless ticket generation, emphasizing that `call_next` consumes tickets in strict issuance order. |
| **II. Fair Service Dispatch & Longest-Waiting Priority** | **PASS** | `DESIGN.md` details how isolated per-service FIFO deques preserve strict arrival precedence and fair customer dispatch without starvation. |
| **III. Non-Mutating State Inspection & Instant Analytics** | **PASS** | `DESIGN.md` contrasts mutating dispatch operations (`call_next`) with non-mutating idempotent operations (`peek_next`), reinforcing Principle III. |
| **IV. Independent Agent & Counter Decoupling** | **PASS** | `DESIGN.md` analyzes multi-counter concurrency, explaining how thread locks and state mutation order isolate counter operations so parallel agents do not interfere with one another. |
| **V. Idiomatic Python & Clean Domain Data Structures** | **PASS** | `DESIGN.md` grounds its analysis directly in Python's standard library primitives (`collections.deque`, `dict`, `threading.Lock`, `enum`). |
| **Domain Integrity & Lifecycle State Machine** | **PASS** | Validates the ticket lifecycle (`ISSUED` -> `WAITING` -> `SERVING` -> `COMPLETED`) and mandates that transition to `SERVING` occurs atomically upon extraction. |
| **Thread & Execution Safety** | **PASS** | Explicitly addresses thread safety in `call_next` under concurrent multi-agent access, identifying race conditions and their resolution. |

**Gate Result**: All Constitution principles and quality gates pass with zero violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-design-notes/
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0 research & architectural findings
├── data-model.md        # Phase 1 conceptual data model & state transition flow
├── quickstart.md        # Phase 1 quickstart validation guide
├── contracts/           # Phase 1 interface & schema contracts
│   └── design-document-contract.md
├── checklists/
│   └── requirements.md
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
branch-queue/
├── DESIGN.md            # The primary artifact created by this feature (Spanish architectural notes)
├── src/
│   ├── cli/
│   │   └── terminal.py
│   ├── exceptions/
│   │   └── errors.py
│   ├── models/
│   │   ├── service_type.py
│   │   ├── stats.py
│   │   └── ticket.py
│   └── services/
│       └── queue_manager.py
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   └── test_queue_manager.py
├── branch_queue.py
├── main.py
└── README.md
```

**Structure Decision**: Single project repository. The deliverable is the root documentation file `DESIGN.md` referencing domain implementations in `src/models/` and `src/services/queue_manager.py`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| *None* | N/A | N/A |
