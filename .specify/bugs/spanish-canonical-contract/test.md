# Bug Verification: Invert Contract to Canonical Spanish Service Types and Parameter Confirmation

- **Slug**: spanish-canonical-contract
- **Tested**: 2026-11-08T10:05:40+01:00
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The original symptom no longer reproduces: `ServiceType` members now expose canonical Spanish values (`"deposito"`, `"retiro"`, `"gestion_cuenta"`), `list_waiting()` and `stats()` output dictionaries with Spanish keys, English inputs resolve seamlessly as aliases, and `issue_ticket`, `peek_next`, and `call_next` accept the `service_type` keyword argument. All 45 tests in the test suite pass with zero regressions.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (post-fix) | `py -c "from src.models.service_type import ServiceType; from src.services.queue_manager import BranchQueueManager; assert ServiceType.DEPOSIT.value == 'deposito'; assert ServiceType.WITHDRAWAL.value == 'retiro'; assert ServiceType.ACCOUNT_MANAGEMENT.value == 'gestion_cuenta'; m = BranchQueueManager(); assert set(m.list_waiting().keys()) == {'deposito', 'retiro', 'gestion_cuenta'}; assert set(m.stats().keys()) == {'deposito', 'retiro', 'gestion_cuenta', 'total'}; t = m.issue_ticket(client_name='Alice', service_type='deposito'); assert m.peek_next(service_type='deposito') == t; print('Reproduction assertions passed!')"` | pass | Verified canonical enum values, dictionary keys in `list_waiting()` and `stats()`, and `service_type` keyword dispatch. |
| New / updated tests | `py -m pytest tests/integration/test_contract_compliance.py tests/unit/test_models.py tests/unit/test_queue_manager.py -v` | pass | 36 test cases passed, covering canonical Spanish names, alias mappings, and keyword arguments. |
| Regression suite | `py -m pytest -v` | pass | All 45 test cases passed across unit, integration, and terminal CLI suites. |
| Lint / type-check | `py -m ruff check src tests` / `flake8` | not-run | Project environment does not configure or install an external linter/type-checker. |

## Output Excerpts

### Post-Fix Reproduction Script
```text
Reproduction assertions passed!
```

### New / Updated Tests (`pytest tests/integration/test_contract_compliance.py tests/unit/test_models.py tests/unit/test_queue_manager.py -v`)
```text
tests/integration/test_contract_compliance.py::test_contract_service_naming PASSED [  5%]
tests/integration/test_contract_compliance.py::test_contract_english_aliases_resolution PASSED [  8%]
tests/integration/test_contract_compliance.py::test_contract_list_waiting_returns_dict_by_service PASSED [ 13%]
tests/integration/test_contract_compliance.py::test_contract_stats_includes_total_count PASSED [ 16%]
tests/integration/test_contract_compliance.py::test_contract_keyword_arguments_service_type PASSED [ 19%]
tests/unit/test_models.py::test_service_type_enum_values PASSED          [ 22%]
tests/unit/test_queue_manager.py::test_list_waiting_specific_service PASSED [ 83%]
tests/unit/test_queue_manager.py::test_list_waiting_all_services PASSED  [ 86%]
tests/unit/test_queue_manager.py::test_stats_method_with_total_and_services PASSED [ 97%]
tests/unit/test_queue_manager.py::test_service_type_keyword_arguments PASSED [100%]
============================= 36 passed in 0.18s ==============================
```

### Full Regression Suite (`pytest -v`)
```text
============================= 45 passed in 0.12s ==============================
```

## Residual Risks

- **Breaking Contract for English-Key Dependent Callers**: External clients expecting English keys (`"deposit"`, `"withdrawal"`, `"account_management"`) in `list_waiting()` or `stats()` dictionaries will need to migrate to the canonical Spanish keys (`"deposito"`, `"retiro"`, `"gestion_cuenta"`), which is the intended specification behavior.

## Recommendation

Close the bug — verified end-to-end. The Spanish canonical contract and `service_type` keyword arguments are validated across reproduction steps and the full automated test suite.

