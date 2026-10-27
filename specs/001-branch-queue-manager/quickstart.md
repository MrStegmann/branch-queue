# Quickstart Validation Guide: Banco Meridional Queue Manager

**Feature Branch**: `001-branch-queue-manager`  
**Date**: 2026-10-27  

---

## 1. Prerequisites & Environment Setup

- **Python Version**: Python 3.11+ (verified on Python 3.14).
- **Dependencies**: Python standard library only.
- **Testing Tool**: `pytest` (`python -m pytest`).

Verify environment:
```bash
python --version
python -m pytest --version
```

---

## 2. Running Automated Tests

Run the full automated test suite to verify domain logic, FIFO fairness, sequence monotonicity, edge cases, and CLI handlers:

```bash
# Run all unit and integration tests
python -m pytest tests/ -v

# Run with test coverage report (if pytest-cov available, otherwise standard pytest)
python -m pytest tests/
```

---

## 3. End-to-End Validation Scenarios

### Scenario 1: Monotonic Ticket Issuance Across Services (P1)
**Goal**: Verify tickets increment globally ($1, 2, 3 \dots$) regardless of service category and that invalid inputs do not advance the counter.

1. Launch Python interactive session or test script:
   ```python
   from src.services.queue_manager import BranchQueueManager
   from src.models.service_type import ServiceType

   mgr = BranchQueueManager()
   t1 = mgr.issue_ticket("Alice", ServiceType.DEPOSIT)
   t2 = mgr.issue_ticket("Bob", ServiceType.WITHDRAWAL)
   t3 = mgr.issue_ticket("Charlie", ServiceType.DEPOSIT)
   ```
2. **Expected Verification**:
   - `t1.number == 1` and `t1.service_type == ServiceType.DEPOSIT`
   - `t2.number == 2` and `t2.service_type == ServiceType.WITHDRAWAL`
   - `t3.number == 3` and `t3.service_type == ServiceType.DEPOSIT`
3. Test invalid issuance:
   ```python
   try:
       mgr.issue_ticket("", "deposit")
   except Exception as e:
       print("Rejected empty name:", e)

   t4 = mgr.issue_ticket("Daniel", ServiceType.ACCOUNT_MANAGEMENT)
   assert t4.number == 4  # Counter did not advance on failure!
   ```

---

### Scenario 2: Service-Specific FIFO Dispatch & Queue Isolation (P1)
**Goal**: Verify tellers dequeue the longest-waiting client for their specific line without disturbing other lines.

1. Issue tickets:
   - Alice (Deposit, T1)
   - Bob (Withdrawal, T2)
   - Charlie (Deposit, T3)
2. Deposit agent calls next:
   ```python
   served = mgr.call_next(ServiceType.DEPOSIT)
   assert served.client_name == "Alice"
   assert served.number == 1
   ```
3. Deposit agent calls next again:
   ```python
   served2 = mgr.call_next(ServiceType.DEPOSIT)
   assert served2.client_name == "Charlie"
   assert served2.number == 3
   ```
4. Withdrawal queue remains intact:
   ```python
   served_w = mgr.call_next(ServiceType.WITHDRAWAL)
   assert served_w.client_name == "Bob"
   assert served_w.number == 2
   ```

---

### Scenario 3: Non-Mutating Peek & Queue Inspection (P2)
**Goal**: Confirm peeking and listing never mutate queue depth, ordering, or timestamps.

1. Queue state: Charlie is waiting for Deposit.
2. Peek next:
   ```python
   peeked1 = mgr.peek_next(ServiceType.DEPOSIT)
   peeked2 = mgr.peek_next(ServiceType.DEPOSIT)
   assert peeked1 == peeked2
   assert len(mgr.list_waiting(ServiceType.DEPOSIT)) == 1
   ```
3. Peek empty queue:
   ```python
   assert mgr.peek_next(ServiceType.ACCOUNT_MANAGEMENT) is None
   assert mgr.call_next(ServiceType.ACCOUNT_MANAGEMENT) is None
   ```

---

### Scenario 4: Real-Time Branch Statistics (P2)
**Goal**: Verify accurate counts per category and total active waiting volume.

1. Query stats:
   ```python
   stats = mgr.get_stats()
   print(stats.counts_by_service)
   print("Total waiting:", stats.total_waiting)
   ```
2. **Expected Verification**:
   - `stats.total_waiting == sum(stats.counts_by_service.values())`
   - Dispatching a ticket immediately decrements counts in $O(1)$ time.

---

### Scenario 5: Interactive Terminal Session Walkthrough (P3)
**Goal**: Verify interactive user experience, menu navigation, input guards, and clean exit.

1. Launch terminal app:
   ```bash
   python -m src.cli.terminal
   ```
2. Follow steps:
   - Select `1` -> Issue ticket for client "Alice" with service `deposit`.
   - Select `1` -> Issue ticket for client "Bob" with service `withdrawal`.
   - Select `4` -> View waiting queues (Alice under Deposit, Bob under Withdrawal).
   - Select `3` -> Peek next client for `deposit` (shows Alice, remains in queue).
   - Select `2` -> Call next client for `deposit` (Alice is called and dequeued).
   - Select `5` -> View statistics (Deposit: 0, Withdrawal: 1, Total: 1).
   - Select `6` -> Exit application cleanly.

---

## 4. Reference Links

- **Domain Model Details**: See [data-model.md](file:///j:/GitHub/branch-queue/specs/001-branch-queue-manager/data-model.md)
- **Programmatic API Contract**: See [queue-api-contract.md](file:///j:/GitHub/branch-queue/specs/001-branch-queue-manager/contracts/queue-api-contract.md)
- **Terminal CLI Contract**: See [cli-contract.md](file:///j:/GitHub/branch-queue/specs/001-branch-queue-manager/contracts/cli-contract.md)
- **Algorithmic Research & Justification**: See [research.md](file:///j:/GitHub/branch-queue/specs/001-branch-queue-manager/research.md)
