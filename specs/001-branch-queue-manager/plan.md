# Implementation Plan: Banco Meridional Queue Manager

**Branch**: `001-branch-queue-manager` | **Date**: 2026-10-27 | **Spec**: [specs/001-branch-queue-manager/spec.md](file:///j:/GitHub/branch-queue/specs/001-branch-queue-manager/spec.md)

**Input**: Feature specification from `specs/001-branch-queue-manager/spec.md`

---

## Summary

The Banco Meridional Queue Manager is a terminal-based queue management system engineered to automate customer flow, eliminate teller idle time, and maintain strict FIFO fairness across distinct banking service categories (`deposit`, `withdrawal`, `account_management`).

The technical design employs isolated `collections.deque` instances for each service category, an atomic post-validation monotonic ticket counter, frozen immutable domain records, and thread-synchronized dispatch operations ensuring $O(1)$ enqueue, dequeue, peek, and real-time statistics generation.

---

## Technical Context

**Language/Version**: Python 3.11+ (running on Python 3.14.7)  
**Primary Dependencies**: None (Standard Library only: `collections.deque`, `dataclasses`, `enum`, `threading`, `datetime`, `typing`, `sys`)  
**Storage**: In-memory data structures (isolated deques and thread-safe sequence counter)  
**Testing**: `pytest` (`python -m pytest tests/`)  
**Target Platform**: Cross-platform terminal (Windows PowerShell/CMD, Linux, macOS)  
**Project Type**: CLI Application with Domain Library Architecture  
**Performance Goals**: Instantaneous $O(1)$ operations for `issue_ticket`, `call_next`, `peek_next`, and `get_stats` regardless of total branch volume  
**Constraints**: Zero external runtime dependencies; zero unhandled crash exceptions on empty queues or invalid user inputs; strictly non-mutating query operations  
**Scale/Scope**: Single branch operational day (up to thousands of client tickets per session)  

---

## Constitution Check

*GATE: Evaluated and Passed against Constitution v1.0.0*

| Principle / Rule | Compliance Status | Architectural Guarantee |
| :--- | :---: | :--- |
| **I. Deterministic Sequential Ticket Issuance** | **PASS** | Monotonic integer sequence counter incremented only after input validation; immutable timestamp and frozen `Ticket` records. |
| **II. Fair Service Dispatch & Longest-Waiting Priority** | **PASS** | Dedicated `collections.deque` per service guarantees strict FIFO order ($O(1)$ popleft) without queue interference. |
| **III. Non-Mutating State Inspection & Instant Analytics** | **PASS** | `peek_next()` reads index 0 without pop; `list_waiting()` returns defensive copies; `get_stats()` calculates lengths in $O(1)$ without queue mutation. |
| **IV. Independent Agent & Counter Decoupling** | **PASS** | Parallel tellers can dispatch independently across services; synchronization locks prevent double-dispatch race conditions within the same service line. |
| **V. Idiomatic Python & Clean Domain Data Structures** | **PASS** | Python standard library primitives only (`dataclasses`, `enum`, `deque`, `threading`); full type annotations; no bloat. |
| **Domain Integrity & Service Constraints** | **PASS** | Explicit `ServiceType` enum with case-insensitive normalization; non-empty client name validation; deterministic lifecycle states. |
| **Quality Gates & Verification Standards** | **PASS** | Automated test suite covering edge cases (empty queues, invalid names, concurrent calls) with mockable time providers. |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-branch-queue-manager/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0 research & algorithmic analysis
├── data-model.md        # Phase 1 domain entities & state machines
├── quickstart.md        # Phase 1 runnable validation scenarios
├── contracts/           # Phase 1 interface contracts
│   ├── queue-api-contract.md # Programmatic Python API specification
│   └── cli-contract.md       # Interactive Terminal menu specification
└── tasks.md             # Phase 2 task checklist (generated via /speckit-tasks)
```

### Source Code Layout

```text
src/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── service_type.py      # ServiceType enum and normalization
│   ├── ticket.py            # Frozen Ticket domain record and TicketStatus enum
│   └── stats.py             # QueueStats dataclass
├── services/
│   ├── __init__.py
│   └── queue_manager.py     # BranchQueueManager domain coordinator
├── exceptions/
│   ├── __init__.py
│   └── errors.py            # Domain exception hierarchy
└── cli/
    ├── __init__.py
    └── terminal.py          # Interactive terminal UI loop and menus

tests/
├── __init__.py
├── conftest.py              # Shared fixtures and mock time providers
├── unit/
│   ├── test_models.py       # Entity validation and immutability tests
│   └── test_queue_manager.py# FIFO dispatch, monotonic sequence, peek, and stats tests
└── integration/
    ├── test_concurrency.py  # Thread-safety and race condition prevention tests
    └── test_terminal_cli.py # CLI menu loop and resilient input handling tests
```

**Structure Decision**: Clean domain library architecture with isolated CLI interface layer and segregated unit/integration test suites.

---

## Complexity Tracking

> **Constitution Check passed with zero violations.** No architectural complexity deviations require justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| *None* | N/A | Fully compliant with Constitution v1.0.0 |
