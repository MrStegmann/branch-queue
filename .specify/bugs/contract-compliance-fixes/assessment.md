# Bug Assessment: Unmet API and Packaging Contract Specifications

- **Slug**: contract-compliance-fixes
- **Created**: 2026-11-03T10:45:00+01:00
- **Source**: pasted text
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

> "The logic is sound: FIFO queues per service, global numbering, a lock for concurrent `call_next` calls—an excellent design overall. HOWEVER, you have not met the specified contract: use `deposit`/`withdrawal`/`account_management` instead of `deposito`/`retiro`/`gestion_cuenta`; `call_next()` must raise an error if the queue is empty (currently it returns `None`); `list_waiting()` must return a dictionary organized by service; `stats()` must include a "total" count; and `branch_queue.py` is missing from the root directory."

## Symptom

Callers, graders, and external client code that adhere to the specified contract encounter multiple failures:
1. Attempting `import branch_queue` or `from branch_queue import ...` fails with `ModuleNotFoundError` because `branch_queue.py` does not exist in the root directory.
2. Invoking `call_next()` on an empty service queue returns `None` instead of raising an error.
3. Invoking `list_waiting()` returns a flat `list[Ticket]` instead of a `dict` mapping service names to their respective lists of waiting tickets.
4. Calling `stats()` fails with `AttributeError` (the implementation exposes `get_stats()` returning a dataclass), and the metrics output lacks a `"total"` count key alongside service counts.
5. Inconsistent naming expectations if Spanish terms (`deposito`, `retiro`, `gestion_cuenta`) were ever referenced, whereas the contract strictly mandates English keys (`deposit`, `withdrawal`, `account_management`).

## Reproduction

1. **Root Module Missing**:
   ```bash
   python -c "import branch_queue"
   ```
   *Result*: `ModuleNotFoundError: No module named 'branch_queue'`.

2. **`call_next()` Empty Queue Behavior**:
   ```python
   from src.services.queue_manager import BranchQueueManager
   manager = BranchQueueManager()
   res = manager.call_next("deposit")
   assert res is None  # Contract requires raising an error when queue is empty!
   ```

3. **`list_waiting()` Return Structure**:
   ```python
   from src.services.queue_manager import BranchQueueManager
   manager = BranchQueueManager()
   manager.issue_ticket("Alice", "deposit")
   waiting = manager.list_waiting()
   assert isinstance(waiting, list)  # Contract requires a dictionary organized by service!
   ```

4. **`stats()` and "total" count**:
   ```python
   from src.services.queue_manager import BranchQueueManager
   manager = BranchQueueManager()
   # manager.stats() does not exist; only manager.get_stats() exists, returning QueueStats dataclass without a "total" dictionary key
   ```

## Suspected Code Paths

- `branch_queue.py` (root directory, missing): Does not exist; external contract expects root-level access.
- `src/services/queue_manager.py:83-107`: `call_next()` returns `None` on empty queue instead of raising an error.
- `src/services/queue_manager.py:133-163`: `list_waiting()` returns `list[Ticket]` rather than `dict[str, list[Ticket]]` organized by service.
- `src/services/queue_manager.py:164-188`: Exposes `get_stats() -> QueueStats` instead of `stats()` returning a dictionary with service keys and a `"total"` count.
- `src/exceptions/errors.py`: Lacks `EmptyQueueError` (or appropriate domain exception) to represent empty queue dispatch failures.
- `src/models/service_type.py:8-56`: Must ensure canonical service keys are strictly `"deposit"`, `"withdrawal"`, and `"account_management"`, with normalization/aliases.
- `src/cli/terminal.py:78-97`: CLI handles `call_next()` returning `None`; must handle the exception raised on empty queue.
- `tests/unit/test_queue_manager.py`: Asserts `call_next()` returning `None` and `list_waiting()` returning lists, which conflict with the required contract.

## Root Cause Hypothesis

High confidence. The system was designed against an earlier or divergent local specification (`specs/001-branch-queue-manager/contracts/queue-api-contract.md`) where `call_next` returned `Optional[Ticket]`, `list_waiting` returned a flat chronologically sorted list, metrics were retrieved via `get_stats() -> QueueStats`, and package modules were strictly nested under `src/`. The actual operational contract mandates root-level module importability (`branch_queue.py`), explicit exception raising on empty dequeues, service-keyed dictionary grouping for waiting tickets, and a `stats()` method returning a `"total"` count under standard English service designations.

## Proposed Remediation

**Preferred**:
1. Create `branch_queue.py` in the root directory that exports the primary classes, exceptions, and models (`BranchQueueManager`, `ServiceType`, `Ticket`, `QueueStats`, `EmptyQueueError`, etc.) or acts as the root module wrapper.
2. Define `EmptyQueueError(QueueOperationError)` in `src/exceptions/errors.py`.
3. In `BranchQueueManager.call_next(service)`:
   - When the target service queue is empty, raise `EmptyQueueError(f"No clients waiting for service '{resolved_service.value}'.")`.
4. In `BranchQueueManager.list_waiting(service=None)`:
   - Return a dictionary organized by service, e.g.:
     `{"deposit": [...], "withdrawal": [...], "account_management": [...]}`.
   - If a specific service filter is passed, return `{resolved_service.value: [...]}` (or the tickets for that service within the dictionary structure).
5. Add/update `stats()` on `BranchQueueManager`:
   - Return a dictionary with service counts and `"total"`, e.g.:
     `{"deposit": x, "withdrawal": y, "account_management": z, "total": sum}`.
   - Retain `get_stats()` as a compatibility helper if needed.
6. Ensure service enum values strictly map to `"deposit"`, `"withdrawal"`, `"account_management"`, and support case-insensitive normalization and alias resolution.
7. Update `src/cli/terminal.py` to catch `EmptyQueueError` and display the existing user-friendly message `[INFO] No clients are currently waiting for '<service>'.`
8. Update existing tests in `tests/unit/test_queue_manager.py` and `tests/integration/test_terminal_cli.py` to test the new contract behaviors, and add integration tests verifying `branch_queue` root importability and API contract compliance.

**Alternatives**:
- *Subclass / Adapter in `branch_queue.py`*: Implement an adapter in `branch_queue.py` while keeping `src.services.queue_manager` unchanged. However, having divergent behavior between `branch_queue` and `src.services.queue_manager` introduces confusion and maintenance overhead; modifying the core service directly is cleaner and ensures single source of truth.

**Files likely to change**:
- `branch_queue.py` (new root file)
- `src/exceptions/errors.py`
- `src/exceptions/__init__.py`
- `src/services/queue_manager.py`
- `src/cli/terminal.py`
- `tests/unit/test_queue_manager.py`
- `tests/integration/test_terminal_cli.py`

**Tests to add or update**:
- Test importing `BranchQueueManager` from `branch_queue`.
- Test `call_next()` raises `EmptyQueueError` when queue is empty.
- Test `list_waiting()` returns a dict organized by service categories.
- Test `stats()` returns dictionary containing `"deposit"`, `"withdrawal"`, `"account_management"`, and `"total"`.
- Test terminal CLI continues to handle empty queue dispatch gracefully.

## Risks & Considerations

- **Breaking API Changes**: Any external code currently expecting `call_next()` to return `None` or `list_waiting()` to return a list will need to handle the new return types and exceptions.
- **CLI Exception Handling**: If the CLI does not catch `EmptyQueueError`, selecting "Call Next Client" on an empty line would crash the interactive menu session.

## Open Questions

- None. The contract requirements from the evaluation feedback are clear and actionable.

