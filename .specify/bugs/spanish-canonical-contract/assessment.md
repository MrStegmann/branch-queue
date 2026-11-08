# Bug Assessment: Invert Contract to Canonical Spanish Service Types and Parameter Confirmation

- **Slug**: spanish-canonical-contract
- **Created**: 2026-11-08T09:50:00+01:00
- **Source**: pasted text
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

> "# Bocking issue
> ## Overview
> The specification requires "deposito", "retiro", and "gestion_cuenta" as canonical values, not as aliases. Invert the contract: use Spanish as the primary language—including for the keys in `list_waiting()` and `stats()`—and treat English only as aliases. Confirm `issue_ticket(client_name, service_type)` and `peek_next(service_type)`"

## Symptom

The current codebase treats English strings (`"deposit"`, `"withdrawal"`, `"account_management"`) as canonical `ServiceType` enum values and as primary dictionary keys in `list_waiting()` and `stats()`, with Spanish terms treated merely as input aliases in `ServiceType.from_string()`.

Callers, automated grading harnesses, and client applications adhering to the specification experience the following failures:
1. `ServiceType` canonical values do not equal `"deposito"`, `"retiro"`, or `"gestion_cuenta"`.
2. `list_waiting()` returns a dictionary with English keys (`"deposit"`, `"withdrawal"`, `"account_management"`) instead of Spanish canonical keys (`"deposito"`, `"retiro"`, `"gestion_cuenta"`).
3. `stats()` returns a dictionary with English service keys (`"deposit"`, `"withdrawal"`, `"account_management"`, `"total"`) instead of Spanish service keys (`"deposito"`, `"retiro"`, `"gestion_cuenta"`, `"total"`).
4. Invoking `manager.issue_ticket(client_name="...", service_type="...")` or `manager.peek_next(service_type="...")` with the keyword argument `service_type` raises `TypeError: ... got an unexpected keyword argument 'service_type'` because the parameter is currently named `service` in `BranchQueueManager`.

## Reproduction

1. **Canonical Service Enum Values**:
   ```python
   from branch_queue import ServiceType
   assert ServiceType.DEPOSIT.value == "deposito"  # Fails: actual is "deposit"
   assert ServiceType.WITHDRAWAL.value == "retiro"  # Fails: actual is "withdrawal"
   assert ServiceType.ACCOUNT_MANAGEMENT.value == "gestion_cuenta"  # Fails: actual is "account_management"
   ```

2. **`list_waiting()` Dictionary Keys**:
   ```python
   from branch_queue import BranchQueueManager
   manager = BranchQueueManager()
   waiting = manager.list_waiting()
   assert set(waiting.keys()) == {"deposito", "retiro", "gestion_cuenta"}
   # Fails: actual keys are {"deposit", "withdrawal", "account_management"}
   ```

3. **`stats()` Dictionary Keys**:
   ```python
   from branch_queue import BranchQueueManager
   manager = BranchQueueManager()
   stats = manager.stats()
   assert set(stats.keys()) == {"deposito", "retiro", "gestion_cuenta", "total"}
   # Fails: actual keys are {"deposit", "withdrawal", "account_management", "total"}
   ```

4. **Keyword Argument `service_type` in `issue_ticket` and `peek_next`**:
   ```python
   from branch_queue import BranchQueueManager
   manager = BranchQueueManager()
   # Attempting to call with specified parameter name:
   manager.issue_ticket(client_name="Alice", service_type="deposito")
   # Fails: TypeError: BranchQueueManager.issue_ticket() got an unexpected keyword argument 'service_type'

   manager.peek_next(service_type="deposito")
   # Fails: TypeError: BranchQueueManager.peek_next() got an unexpected keyword argument 'service_type'
   ```

## Suspected Code Paths

- `src/models/service_type.py:8-14`: Defines `ServiceType(str, Enum)` with values `"deposit"`, `"withdrawal"`, and `"account_management"`. Must be inverted to canonical Spanish: `"deposito"`, `"retiro"`, `"gestion_cuenta"`.
- `src/models/service_type.py:44-58`: `ServiceType.from_string()` contains Spanish alias dictionary mapping to English values; must be inverted so English strings (`"deposit"`, `"withdrawal"`, `"account_management"`, `"account management"`) map to canonical Spanish enum members, while retaining accent normalization (`"depósito"`, `"gestión_cuenta"`).
- `src/services/queue_manager.py:46`: `issue_ticket(self, client_name: str, service: Union[str, ServiceType])` uses parameter name `service` instead of `service_type`.
- `src/services/queue_manager.py:112`: `peek_next(self, service: Union[str, ServiceType])` uses parameter name `service` instead of `service_type`.
- `src/services/queue_manager.py:83`: `call_next(self, service: Union[str, ServiceType])` uses parameter name `service` (should also accept `service_type` for parameter naming symmetry).
- `src/services/queue_manager.py:136-169`: `list_waiting()` constructs output keys using `ServiceType.*.value` (will output Spanish keys once enum is updated, but also needs to support filtering by both Spanish and English aliases).
- `src/services/queue_manager.py:170-191`: `stats()` constructs output keys using `ServiceType.*.value` plus `"total"`.
- `src/cli/terminal.py:21-38, 40-50, 131-147`: CLI menus, prompt validation, and list display format service names.
- `tests/integration/test_contract_compliance.py`: Hardcodes assertions against English keys `"deposit"`, `"withdrawal"`, `"account_management"`.
- `tests/unit/test_models.py` & `tests/unit/test_queue_manager.py`: Unit test assertions verify English enum values and keys.

## Root Cause Hypothesis

High confidence. The previous contract compliance pass (`contract-compliance-fixes`) aligned the codebase with English canonical keys based on an earlier specification interpretation. However, the authoritative operational contract specifies Spanish (`"deposito"`, `"retiro"`, `"gestion_cuenta"`) as canonical values and dictionary keys in `list_waiting()` and `stats()`, with English treated as aliases. In addition, `BranchQueueManager.issue_ticket` and `BranchQueueManager.peek_next` were implemented with parameter name `service` rather than `service_type`, causing keyword-argument calls expecting `service_type` to fail with a `TypeError`.

## Proposed Remediation

**Preferred**:
1. **Invert `ServiceType` Canonical Values in `src/models/service_type.py`**:
   - Set enum values to canonical Spanish:
     ```python
     class ServiceType(str, Enum):
         DEPOSIT = "deposito"
         WITHDRAWAL = "retiro"
         ACCOUNT_MANAGEMENT = "gestion_cuenta"
     ```
   - Provide Spanish alias member attributes if helpful (e.g. `DEPOSITO = "deposito"`, `RETIRO = "retiro"`, `GESTION_CUENTA = "gestion_cuenta"`).
   - In `ServiceType.from_string()`:
     - Map English aliases (`"deposit"`, `"withdrawal"`, `"account_management"`, `"account management"`) to the canonical enum members.
     - Retain accented Spanish variants (`"depósito"`, `"gestión_cuenta"`, `"gestión de cuenta"`, `"gestión"`) and numeric shortcuts (`"1"`, `"2"`, `"3"`).
2. **Update Method Signatures in `src/services/queue_manager.py`**:
   - Update `issue_ticket`:
     ```python
     def issue_ticket(
         self,
         client_name: str,
         service_type: Optional[Union[str, ServiceType]] = None,
         *,
         service: Optional[Union[str, ServiceType]] = None,
     ) -> Ticket:
     ```
     Allowing `service_type` as a positional or keyword argument, with `service` accepted as a backward-compatible keyword alias.
   - Update `peek_next`:
     ```python
     def peek_next(
         self,
         service_type: Optional[Union[str, ServiceType]] = None,
         *,
         service: Optional[Union[str, ServiceType]] = None,
     ) -> Optional[Ticket]:
     ```
     Supporting both positional and keyword invocation with `service_type` or `service`.
   - Update `call_next`:
     ```python
     def call_next(
         self,
         service_type: Optional[Union[str, ServiceType]] = None,
         *,
         service: Optional[Union[str, ServiceType]] = None,
     ) -> Ticket:
     ```
     Supporting `service_type` and `service` interchangeably.
3. **Ensure `list_waiting()` and `stats()` Use Canonical Spanish Keys**:
   - `list_waiting()` returns `{"deposito": [...], "retiro": [...], "gestion_cuenta": [...]}`.
   - When filtering by service (e.g. `manager.list_waiting("deposit")`), resolve the service alias and return `{resolved_service.value: [...]}` (i.e. `{"deposito": [...]}`).
   - `stats()` returns `{"deposito": x, "retiro": y, "gestion_cuenta": z, "total": total}`.
4. **Update CLI and Display Strings in `src/cli/terminal.py`**:
   - Ensure CLI service selection and display remain friendly while using canonical Spanish keys under the hood.
5. **Update Test Suites**:
   - Update `tests/integration/test_contract_compliance.py` to assert canonical Spanish keys, English alias resolution, and keyword argument calls for `issue_ticket(client_name=..., service_type=...)` and `peek_next(service_type=...)`.
   - Update `tests/unit/test_models.py` and `tests/unit/test_queue_manager.py` for canonical Spanish values and dictionary structures.

**Alternatives**:
- *Strict positional-only signatures*: Changing parameter names directly to `(self, client_name: str, service_type: Union[str, ServiceType])` without backward compatibility for `service`. While cleaner, supporting both `service_type` and `service` via kwargs prevents breaking any internal callers that passed `service=...`.

**Files likely to change**:
- `src/models/service_type.py`
- `src/services/queue_manager.py`
- `src/cli/terminal.py`
- `tests/integration/test_contract_compliance.py`
- `tests/unit/test_models.py`
- `tests/unit/test_queue_manager.py`

**Tests to add or update**:
- Contract tests verifying `ServiceType.DEPOSIT.value == "deposito"`, `ServiceType.WITHDRAWAL.value == "retiro"`, `ServiceType.ACCOUNT_MANAGEMENT.value == "gestion_cuenta"`.
- Verification that English strings `"deposit"`, `"withdrawal"`, `"account_management"` successfully resolve as aliases.
- Verification that `list_waiting()` returns dictionary keys `{"deposito", "retiro", "gestion_cuenta"}`.
- Verification that `stats()` returns dictionary keys `{"deposito", "retiro", "gestion_cuenta", "total"}`.
- Test `issue_ticket(client_name="Alice", service_type="deposito")` and `issue_ticket("Alice", "deposito")`.
- Test `peek_next(service_type="deposito")` and `peek_next("deposito")`.

## Risks & Considerations

- **Breaking Changes for English-Key Dependent Callers**: Any code expecting English keys in `list_waiting()` or `stats()` will break unless updated or alias-mapped. Since this is an explicit contract inversion requested by the specification, this change is intentional.
- **Queue State Isolation & Concurrency**: The internal queuing and threading mechanisms remain unchanged; only key mapping and parameter resolution are affected.

## Open Questions

- None. The requirement explicitly defines canonical Spanish values (`"deposito"`, `"retiro"`, `"gestion_cuenta"`), English as aliases, dictionary keys in `list_waiting()` and `stats()`, and confirmation of `issue_ticket(client_name, service_type)` and `peek_next(service_type)`.

