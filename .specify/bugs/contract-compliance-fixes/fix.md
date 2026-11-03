# Bug Fix: Contract Compliance Fixes for API and Packaging

- **Slug**: contract-compliance-fixes
- **Fixed**: 2026-11-03T11:00:00+01:00
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Aligned `BranchQueueManager` and repository packaging with the specified public contract by creating root `branch_queue.py`, raising `EmptyQueueError` on empty `call_next()`, organizing `list_waiting()` output by service category in a dictionary, adding `stats()` with total count, and normalizing Spanish service name aliases to standard English keys.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `branch_queue.py` | added | Root entrypoint and export wrapper for library callers and direct script execution |
| `src/exceptions/errors.py` | modified | Defined `EmptyQueueError(QueueOperationError)` |
| `src/exceptions/__init__.py` | modified | Exported `EmptyQueueError` |
| `src/models/service_type.py` | modified | Added Spanish alias normalization (`deposito`, `retiro`, `gestion_cuenta`) in `from_string` |
| `src/services/queue_manager.py` | modified | Raised `EmptyQueueError` on empty dequeue in `call_next()`, structured `list_waiting()` as service-grouped dict, added `stats()` method returning service counts and `"total"` |
| `src/cli/terminal.py` | modified | Caught `EmptyQueueError` during dispatch and updated waiting list rendering to consume dictionary structure |
| `tests/unit/test_queue_manager.py` | modified | Updated tests to assert `EmptyQueueError` and dictionary return structure, added `test_stats_method_with_total_and_services` |
| `tests/unit/test_models.py` | modified | Added test cases for Spanish alias normalization |
| `tests/integration/test_concurrency.py` | modified | Updated concurrent teller loop to catch `EmptyQueueError` on queue exhaustion |
| `tests/integration/test_contract_compliance.py` | added | End-to-end integration tests verifying root module import and public API contract requirements |

## Diff Highlights (optional)

```python
# src/services/queue_manager.py
    def call_next(self, service: Union[str, ServiceType]) -> Ticket:
        resolved_service = ServiceType.from_string(service)
        with self._lock:
            q = self._queues[resolved_service]
            if not q:
                raise EmptyQueueError(
                    f"No clients waiting for service '{resolved_service.value}'."
                )
            return q.popleft()

    def list_waiting(
        self, service: Optional[Union[str, ServiceType]] = None
    ) -> Dict[str, List[Ticket]]:
        if service is not None:
            resolved_service = ServiceType.from_string(service)
            with self._lock:
                return {resolved_service.value: list(self._queues[resolved_service])}

        with self._lock:
            return {
                ServiceType.DEPOSIT.value: list(self._queues[ServiceType.DEPOSIT]),
                ServiceType.WITHDRAWAL.value: list(self._queues[ServiceType.WITHDRAWAL]),
                ServiceType.ACCOUNT_MANAGEMENT.value: list(
                    self._queues[ServiceType.ACCOUNT_MANAGEMENT]
                ),
            }

    def stats(self) -> Dict[str, int]:
        with self._lock:
            deposit_count = len(self._queues[ServiceType.DEPOSIT])
            withdrawal_count = len(self._queues[ServiceType.WITHDRAWAL])
            account_management_count = len(self._queues[ServiceType.ACCOUNT_MANAGEMENT])
            return {
                ServiceType.DEPOSIT.value: deposit_count,
                ServiceType.WITHDRAWAL.value: withdrawal_count,
                ServiceType.ACCOUNT_MANAGEMENT.value: account_management_count,
                "total": deposit_count + withdrawal_count + account_management_count,
            }
```

## Tests Added or Updated

- `tests/integration/test_contract_compliance.py::test_root_module_exports` — Verifies `import branch_queue` exports all required classes, enums, and exceptions.
- `tests/integration/test_contract_compliance.py::test_contract_service_naming` — Verifies canonical service enum values strictly match `"deposit"`, `"withdrawal"`, `"account_management"`.
- `tests/integration/test_contract_compliance.py::test_contract_call_next_raises_empty_queue_error` — Pins down `EmptyQueueError` raising when calling next on an empty queue.
- `tests/integration/test_contract_compliance.py::test_contract_list_waiting_returns_dict_by_service` — Confirms `list_waiting()` returns a service-keyed dictionary.
- `tests/integration/test_contract_compliance.py::test_contract_stats_includes_total_count` — Verifies `stats()` returns dictionary with `"total"` alongside service counts.
- `tests/unit/test_queue_manager.py::test_call_next_empty_queue_raises_error` — Validates error raising on empty service lines.
- `tests/unit/test_queue_manager.py::test_list_waiting_all_services` — Validates dictionary output structure across services.
- `tests/unit/test_queue_manager.py::test_stats_method_with_total_and_services` — Tests count tracking and `"total"` calculation.
- `tests/unit/test_models.py::test_service_type_from_string_success` — Tests Spanish aliases (`deposito`, `retiro`, `gestion_cuenta`) normalization.
- `tests/integration/test_concurrency.py::test_concurrent_dispatch_no_double_servicing` — Verifies concurrent dispatch handles `EmptyQueueError` gracefully when queues drain.

## Local Verification

- Commands run:
  - `python -m pytest` → 42 passed in 0.18s
  - `python -c "import branch_queue; print([x for x in dir(branch_queue) if not x.startswith('_')])"` → `['BranchQueueError', 'BranchQueueManager', 'EmptyClientNameError', 'EmptyQueueError', 'InvalidServiceTypeError', 'QueueOperationError', 'QueueStats', 'ServiceType', 'Ticket', 'TicketStatus', 'ValidationError', 'main']`
  - `python -c "import subprocess, sys; p = subprocess.run([sys.executable, 'branch_queue.py'], input='6\n', text=True, capture_output=True); print('Exit code:', p.returncode)"` → `Exit code: 0`
- Manual checks: Verified CLI menu interactions and exception handling for empty queue dispatch.

## Deviations from Assessment

None. All remediation items proposed in the assessment were implemented directly according to the evaluation contract.

## Follow-ups

- Run `/speckit-bug-test slug=contract-compliance-fixes` to record formal verification.

