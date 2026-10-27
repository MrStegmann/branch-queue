# Phase 0 Research: Banco Meridional Queue Manager

**Feature Branch**: `001-branch-queue-manager`  
**Date**: 2026-10-27  
**Author**: SpecKit Architecture & Design Workflow  

---

## 1. Executive Summary

Banco Meridional requires a high-performance, terminal-based queue management system that establishes strict fairness, zero agent idle time, and transparent queue oversight prior to deploying physical touchscreen kiosks.

This research document resolves all architectural decisions, algorithmic trade-offs, and domain designs required by the feature specification and Constitution v1.0.0.

---

## 2. Research Decisions & Technical Trade-offs

### 2.1 Queue Data Structure: Isolated FIFO Deques vs. Monolithic List (FR-011)

- **Context**: A branch receives clients for three core services: `deposit`, `withdrawal`, and `account_management`. Clients arrive in arbitrary interleaved order. When a specialized teller calls "next", they must instantly receive the longest-waiting client for that specific service.
- **Alternatives Considered**:
  1. *Monolithic Single Queue (`list[Ticket]`)*: Store all incoming tickets in a single arrival array. When a teller for `deposit` calls next, scan linearly from index 0 for `ticket.service_type == 'deposit'`, remove that element (`list.pop(i)`), and shift all subsequent elements.
  2. *Single Priority Queue (`heapq`)*: Maintain a single min-heap sorted by `(arrival_timestamp, ticket_number)`. To extract the earliest ticket for a specific service, either pop until a match is found (buffering non-matches) or re-heapify after item removal.
  3. *Isolated Service Queues (`dict[ServiceType, collections.deque[Ticket]]`)*: Maintain a dedicated, independent double-ended queue (`collections.deque`) for each service category. Enqueuing appends to the corresponding deque; dispatching pops from the left of the requested deque.
- **Decision**: **Isolated Service Queues using `collections.deque` per `ServiceType`**.
- **Rationale & Complexity Analysis**:
  - **Enqueue ($O(1)$)**: Appending to a `deque` is $O(1)$ amortized memory allocation.
  - **Dispatch ($O(1)$)**: Dequeuing via `deque.popleft()` is strictly $O(1)$, compared to $O(N)$ linear search and array shift in a monolithic list.
  - **Peek ($O(1)$)**: Inspecting `queue[0]` without popping is strictly $O(1)$ and side-effect free.
  - **Isolation**: Work or mutations in `deposit` have zero impact on the memory segments or locks of `withdrawal` and `account_management`.
  - **Constitution Compliance**: Principle II (Fair Service Dispatch & Longest-Waiting Priority) and Principle V (Clean Domain Data Structures using Python stdlib primitives).

| Approach | Enqueue Time | Dispatch Time | Peek Time | Algorithmic Complexity Evaluation |
| :--- | :---: | :---: | :---: | :--- |
| **Isolated `collections.deque`** | $O(1)$ | $O(1)$ | $O(1)$ | **Optimal**: Zero scanning; immediate popleft. |
| Monolithic List | $O(1)$ | $O(N)$ | $O(N)$ | Suboptimal: Requires scanning and shifting array. |
| Monolithic Min-Heap (`heapq`) | $O(\log N)$ | $O(N)$ | $O(N)$ | Inefficient for service-filtered extraction. |

---

### 2.2 Global Monotonic Sequence Counter (FR-001, Constitution Principle I)

- **Context**: Even though service queues are physically isolated, the branch issues a globally unified, contiguous ticket sequence ($1, 2, 3, \dots$) across all services. The sequence must never produce duplicate ticket numbers or gaps when validation fails.
- **Alternatives Considered**:
  1. *Timestamp-based IDs (e.g. `20261027-001` or UUIDv4)*: Non-sequential or complex for human receptionists and clients.
  2. *Service-prefixed Counters (e.g., `DEP-1`, `WTH-1`)*: Violates FR-001 ("monotonic integer ticket number starting at 1 that increases globally across all service categories").
  3. *Atomic Thread-Safe Global Counter*: An integer counter protected by a reentrant or mutual exclusion lock (`threading.Lock`), incremented only *after* full validation of input parameters.
- **Decision**: **Synchronized Atomic Integer Counter with Post-Validation Increment**.
- **Rationale**:
  - Ensures gapless sequence generation: If a client supplies a blank name or invalid service type, validation rejects the request *before* the counter is incremented.
  - Thread-safe increment ensures no two concurrent requests receive the same ticket number.

---

### 2.3 Domain Entity Immutability & Lifecycle Tracking

- **Context**: Tickets must be immutable domain records, while ticket lifecycle transitions must be auditable and observable.
- **Alternatives Considered**:
  1. *Mutable Ticket Class*: Changing `ticket.status = SERVING` in place allows unintended side effects during non-mutating inspection (peek/list).
  2. *Frozen Dataclass with Value Evolution*: Define `Ticket` as `@dataclass(frozen=True)` capturing `(number, client_name, service_type, issued_at)`. Define lifecycle state transitions in service records or return a new `ServingSession` / updated ticket instance upon dispatch.
- **Decision**: **Frozen `Ticket` dataclass representing the issued ticket record**.
- **Rationale**:
  - Guarantees Principle III: Non-mutating state inspection (`peek`, `list`) cannot mutate ticket properties even accidentally.
  - Fields:
    - `number: int` (positive integer $\ge 1$)
    - `client_name: str` (non-empty, trimmed)
    - `service_type: ServiceType` (Enum: `DEPOSIT`, `WITHDRAWAL`, `ACCOUNT_MANAGEMENT`)
    - `issued_at: datetime` (immutable arrival timestamp)

---

### 2.4 Service Categorization & Input Normalization (FR-002, FR-003)

- **Context**: The terminal and programmatic APIs must accept standard service category identifiers while gracefully handling case variations and leading/trailing whitespace.
- **Alternatives Considered**:
  1. *Raw String Keys (`"deposit"`, `"withdrawal"`, `"account_management"`)*: Prone to typo bugs and string comparison mismatches.
  2. *Python Standard `Enum` with Normalization Helper*: An enumeration `ServiceType(str, Enum)` containing `DEPOSIT = "deposit"`, `WITHDRAWAL = "withdrawal"`, `ACCOUNT_MANAGEMENT = "account_management"` with a `from_string(value: str) -> ServiceType` classmethod that strips whitespace and lowers case.
- **Decision**: **`ServiceType(str, Enum)` with `from_string` classmethod**.
- **Rationale**:
  - Provides type safety, auto-completion, and clean validation.
  - Invalid inputs raise an explicit `InvalidServiceTypeError` without mutating any queue state.

---

### 2.5 Concurrency Model & Race Condition Mitigation (FR-012, Constitution Principle IV)

- **Context**: Multiple agents servicing the same category could invoke `call_next()` simultaneously.
- **Race Condition Scenario**:
  - Agent A and Agent B at Counter 1 and Counter 2 both invoke `call_next(ServiceType.DEPOSIT)` at timestamp $T$.
  - Without atomic mutation, both agents could read `deposit_queue[0]` (Ticket #1) simultaneously. Both tellers would call Alice (Ticket #1), creating customer confusion and leaving Ticket #3 waiting unserviced.
- **Mitigation Strategy**:
  - Enclose queue dispatch (`deque.popleft()`) inside a fine-grained synchronization lock (`threading.Lock` per service queue or global manager lock).
  - State mutation (removal from queue) MUST strictly precede any logging, notification, or presentation to the caller.
  - If the queue is empty at the exact moment the lock is acquired, return `None` immediately.

---

### 2.6 Terminal User Interface Architecture (FR-010, User Story 5)

- **Context**: The terminal interface must provide branch staff with a clear, interactive menu that never crashes on invalid input and cleanly routes to domain operations.
- **Architecture**:
  - **Separation of Concerns**: The CLI module (`src/cli/terminal.py`) is decoupled from the domain engine (`src/services/queue_manager.py`).
  - The CLI handles:
    - Menu rendering and option selection
    - Input prompts with validation and descriptive error reporting
    - Formatted tabular display for queue lists and statistics
    - Graceful keyboard interrupt handling (`Ctrl+C` or exit command)
  - The Domain Manager handles:
    - Invariants, sequencing, deque storage, and thread safety.

---

## 3. Technology Stack Alignment

| Dimension | Specification | Notes / Rationale |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ (running on Python 3.14) | Standard library only; no external runtime dependencies. |
| **Core Primitives** | `collections.deque`, `dataclasses`, `enum`, `threading`, `datetime` | Constitution Principle V compliance. |
| **CLI Display** | Pure standard library `sys.stdout`, `input()` | Clean ANSI-compatible formatting without external dependencies like `click` or `rich`. |
| **Testing** | `pytest` (standard unit + property testing) | Automated test suite verifying FIFO discipline, sequential numbers, and edge cases. |

---

## 4. Conclusion & Next Steps

All unknowns and architectural decisions have been resolved. The design proceeds to Phase 1:
1. `data-model.md`: Formal entity schemas, constraints, and state transitions.
2. `contracts/`: CLI interface contract and programmatic Python API contract.
3. `quickstart.md`: Step-by-step verification guide.
