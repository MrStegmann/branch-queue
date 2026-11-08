# Bug Fix: Invert Contract to Canonical Spanish Service Types and Support `service_type` Parameter

- **Slug**: spanish-canonical-contract
- **Fixed**: 2026-11-08T09:58:30+01:00
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Inverted the service contract so that Spanish terms (`"deposito"`, `"retiro"`, `"gestion_cuenta"`) are canonical values in `ServiceType` and primary keys in `list_waiting()` and `stats()`, with English terms treated as aliases. Updated `BranchQueueManager` methods (`issue_ticket`, `peek_next`, `call_next`, `list_waiting`) to support the `service_type` parameter name while retaining backward compatibility with `service`.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/models/service_type.py` | modified | Set canonical enum values to Spanish (`"deposito"`, `"retiro"`, `"gestion_cuenta"`), added Spanish attribute aliases (`DEPOSITO`, `RETIRO`, `GESTION_CUENTA`), and updated `from_string` to map English strings and Spanish accented forms to canonical members. |
| `src/services/queue_manager.py` | modified | Updated `issue_ticket`, `call_next`, `peek_next`, and `list_waiting` parameter signatures to support `service_type` and backward-compatible `service` kwargs; aligned `list_waiting()` and `stats()` dictionary keys to canonical Spanish values. |
| `src/cli/terminal.py` | modified | Updated CLI service selection menu options and validation error messages to reference canonical Spanish service names. |
| `tests/integration/test_contract_compliance.py` | modified | Updated contract tests to assert canonical Spanish values, verify English alias mapping, validate Spanish keys in `list_waiting()` and `stats()`, and test `service_type` keyword arguments. |
| `tests/unit/test_models.py` | modified | Updated enum value assertions to check canonical Spanish strings and member attributes. |
| `tests/unit/test_queue_manager.py` | modified | Updated `list_waiting()` and `stats()` assertions for Spanish keys, and added dedicated test for `service_type` keyword argument dispatch. |

## Diff Highlights (optional)

```python
# src/models/service_type.py
class ServiceType(str, Enum):
    DEPOSIT = "deposito"
    WITHDRAWAL = "retiro"
    ACCOUNT_MANAGEMENT = "gestion_cuenta"

    # Spanish aliases for attribute access
    DEPOSITO = "deposito"
    RETIRO = "retiro"
    GESTION_CUENTA = "gestion_cuenta"
```

```python
# src/services/queue_manager.py
def issue_ticket(
    self,
    client_name: str,
    service_type: Optional[Union[str, ServiceType]] = None,
    *,
    service: Optional[Union[str, ServiceType]] = None,
) -> Ticket:
    raw_service = service_type if service_type is not None else service
    if raw_service is None:
        raise InvalidServiceTypeError("Service type is required.")
    resolved_service = ServiceType.from_string(raw_service)
    ...
```

## Tests Added or Updated

- `tests/integration/test_contract_compliance.py::test_contract_service_naming` — Verifies canonical Spanish values for `ServiceType` and attribute aliases.
- `tests/integration/test_contract_compliance.py::test_contract_english_aliases_resolution` — Pins down English aliases (`deposit`, `withdrawal`, `account_management`) resolving to canonical enum members.
- `tests/integration/test_contract_compliance.py::test_contract_list_waiting_returns_dict_by_service` — Asserts Spanish keys in `list_waiting()` and single-service filtering.
- `tests/integration/test_contract_compliance.py::test_contract_stats_includes_total_count` — Asserts Spanish keys and total count in `stats()`.
- `tests/integration/test_contract_compliance.py::test_contract_keyword_arguments_service_type` — Pins down keyword argument invocation using `service_type` for `issue_ticket`, `peek_next`, and `call_next`.
- `tests/unit/test_models.py::test_service_type_enum_values` — Verifies `ServiceType` enum values match Spanish strings.
- `tests/unit/test_queue_manager.py::test_list_waiting_specific_service` — Verifies Spanish keys in filtered waiting queue dictionary.
- `tests/unit/test_queue_manager.py::test_list_waiting_all_services` — Verifies Spanish keys across all queues.
- `tests/unit/test_queue_manager.py::test_stats_method_with_total_and_services` — Verifies Spanish keys in `manager.stats()`.
- `tests/unit/test_queue_manager.py::test_service_type_keyword_arguments` — Verifies keyword argument `service_type` handling across public manager methods.

## Local Verification

- Commands run: `py -m pytest -v` → 45 passed in 0.24s.
- Manual checks: Verified enum iteration preserves uniqueness and aliases map correctly.

## Deviations from Assessment

None. The remediation followed the assessment's preferred implementation plan.

## Follow-ups

- Run `/speckit-bug-test slug=spanish-canonical-contract` to validate the resolution.

