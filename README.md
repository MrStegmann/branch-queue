# Banco Meridional - Queue Manager

A high-performance, thread-safe terminal-based queue management system engineered for Banco Meridional branch operations. Designed with strict FIFO fairness, zero external runtime dependencies, $O(1)$ operations, and robust terminal input handling.

---

## 🌟 Key Features

- **Deterministic Sequential Ticket Issuance**: Monotonically increasing ticket sequence numbers starting at `#1`, issued atomically without gaps or resets across services.
- **Fair FIFO Service Dispatch**: Dedicated, isolated `collections.deque` instances for each banking service category (`deposit`, `withdrawal`, `account_management`), ensuring tellers dispatch the longest-waiting client with zero cross-queue interference.
- **Non-Mutating Inspection & Analytics**: Instantaneous, side-effect-free queue inspection (`peek_next`), defensive snapshot listings (`list_waiting`), and real-time branch depth metrics (`get_stats`) computed in $O(1)$ time.
- **Concurrency & Thread Safety**: Synchronized atomic operations preventing race conditions or double-servicing across parallel teller desks.
- **Resilient Interactive Terminal Console**: Full keyboard-driven interface with input whitespace trimming, numeric/string service shortcuts, and clean signal handling (`Ctrl+C`, `Ctrl+D`).

---

## 🏗️ Architecture & Technical Stack

- **Language**: Python 3.11+ (Standard Library only)
- **Data Structures**: `collections.deque`, `dataclasses.dataclass(frozen=True)`, `enum.Enum`, `threading.Lock`
- **Testing**: `pytest`
- **No External Runtime Dependencies**: Standard library primitives exclusively for zero bloat, maximum portability, and direct maintainability.

### Project Layout

```text
branch-queue/
├── main.py                  # Root CLI entry point
├── src/
│   ├── models/
│   │   ├── service_type.py  # ServiceType enum with normalization & shortcuts
│   │   ├── ticket.py        # Frozen immutable Ticket record & TicketStatus enum
│   │   └── stats.py         # QueueStats snapshot dataclass
│   ├── services/
│   │   └── queue_manager.py # BranchQueueManager coordinator (FIFO deques, Lock, $O(1)$ API)
│   ├── exceptions/
│   │   └── errors.py        # Domain exception hierarchy (BranchQueueError, ValidationError, etc.)
│   └── cli/
│       └── terminal.py      # Terminal menu loop, formatting, and input guards
├── tests/
│   ├── conftest.py          # Shared fixtures and deterministic time providers
│   ├── unit/
│   │   ├── test_models.py   # Domain model validation and immutability tests
│   │   └── test_queue_manager.py # FIFO dispatch, monotonic numbering, peek, and stats tests
│   └── integration/
│       ├── test_concurrency.py  # Multi-threaded race condition tests
│       └── test_terminal_cli.py # Interactive CLI menu integration tests
└── specs/                   # SpecKit feature documentation & contracts
```

---

## 🚀 Quickstart

### 1. Requirements

- Python 3.11 or higher
- `pytest` (for running test suites)

### 2. Launch Interactive Terminal

Run either of the following commands from the repository root:

```bash
python main.py
```
or
```bash
python -m src.cli.terminal
```

### 3. Terminal Menu Options

```text
============================================================
           BANCO MERIDIONAL - QUEUE MANAGER v1.0
============================================================
1. Issue New Ticket (Client Arrival)
2. Call Next Client (Service Counter Dispatch)
3. Peek Next Client (Non-Mutating Inspection)
4. List All Waiting Clients
5. View Branch Statistics & Queue Depth
6. Exit System
============================================================
```

---

## 🧪 Running Tests

Execute the automated test suite covering unit models, queue operations, concurrency race-condition resistance, and CLI interactions:

```bash
python -m pytest tests/ -v
```

All 36 tests execute in under a quarter-second.

---

## 📖 Specifications & Design Artifacts

For in-depth domain specifications, interface contracts, and architectural decisions:
- [Feature Specification](specs/001-branch-queue-manager/spec.md)
- [Architecture & Implementation Plan](specs/001-branch-queue-manager/plan.md)
- [Domain Data Model](specs/001-branch-queue-manager/data-model.md)
- [Programmatic API Contract](specs/001-branch-queue-manager/contracts/queue-api-contract.md)
- [Terminal CLI Contract](specs/001-branch-queue-manager/contracts/cli-contract.md)
- [Quickstart Guide](specs/001-branch-queue-manager/quickstart.md)
