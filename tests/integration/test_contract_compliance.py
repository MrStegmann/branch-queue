"""Contract compliance tests for API expectations and root module importability."""

import pytest
import branch_queue
from branch_queue import (
    BranchQueueManager,
    ServiceType,
    Ticket,
    EmptyQueueError,
    QueueStats,
)


def test_root_module_exports():
    """branch_queue.py in root must export all necessary domain classes and exceptions."""
    assert hasattr(branch_queue, "BranchQueueManager")
    assert hasattr(branch_queue, "ServiceType")
    assert hasattr(branch_queue, "Ticket")
    assert hasattr(branch_queue, "EmptyQueueError")
    assert hasattr(branch_queue, "QueueStats")
    assert hasattr(branch_queue, "main")


def test_contract_service_naming():
    """Spanish canonical service keys: deposito, retiro, gestion_cuenta."""
    assert ServiceType.DEPOSIT.value == "deposito"
    assert ServiceType.WITHDRAWAL.value == "retiro"
    assert ServiceType.ACCOUNT_MANAGEMENT.value == "gestion_cuenta"
    assert ServiceType.DEPOSITO.value == "deposito"
    assert ServiceType.RETIRO.value == "retiro"
    assert ServiceType.GESTION_CUENTA.value == "gestion_cuenta"


def test_contract_english_aliases_resolution():
    """English strings must resolve as aliases to canonical ServiceType."""
    assert ServiceType.from_string("deposit") == ServiceType.DEPOSIT
    assert ServiceType.from_string("withdrawal") == ServiceType.WITHDRAWAL
    assert ServiceType.from_string("account_management") == ServiceType.ACCOUNT_MANAGEMENT
    assert ServiceType.from_string("account management") == ServiceType.ACCOUNT_MANAGEMENT


def test_contract_call_next_raises_empty_queue_error():
    """call_next() must raise an error if the queue is empty."""
    manager = BranchQueueManager()
    with pytest.raises(EmptyQueueError) as exc_info:
        manager.call_next("deposito")
    assert "No clients waiting" in str(exc_info.value)

    with pytest.raises(EmptyQueueError):
        manager.call_next(ServiceType.WITHDRAWAL)

    with pytest.raises(EmptyQueueError):
        manager.call_next("deposit")

    with pytest.raises(EmptyQueueError):
        manager.call_next("gestion_cuenta")


def test_contract_list_waiting_returns_dict_by_service():
    """list_waiting() must return a dictionary organized by canonical Spanish service keys."""
    manager = BranchQueueManager()
    t1 = manager.issue_ticket("Alice", "deposito")
    t2 = manager.issue_ticket("Bob", "retiro")

    waiting = manager.list_waiting()
    assert isinstance(waiting, dict)
    assert set(waiting.keys()) == {"deposito", "retiro", "gestion_cuenta"}
    assert waiting["deposito"] == [t1]
    assert waiting["retiro"] == [t2]
    assert waiting["gestion_cuenta"] == []

    # Single-service filtering returns canonical Spanish key, accepting English alias
    filtered_sp = manager.list_waiting("deposito")
    assert filtered_sp == {"deposito": [t1]}
    filtered_en = manager.list_waiting("deposit")
    assert filtered_en == {"deposito": [t1]}


def test_contract_stats_includes_total_count():
    """stats() must return a dictionary and include canonical Spanish service keys and 'total' count."""
    manager = BranchQueueManager()
    empty_stats = manager.stats()
    assert isinstance(empty_stats, dict)
    assert empty_stats == {
        "deposito": 0,
        "retiro": 0,
        "gestion_cuenta": 0,
        "total": 0,
    }

    manager.issue_ticket("Alice", "deposito")
    manager.issue_ticket("Bob", "deposit")  # using English alias
    manager.issue_ticket("Charlie", "gestion_cuenta")

    populated_stats = manager.stats()
    assert isinstance(populated_stats, dict)
    assert populated_stats["total"] == 3
    assert populated_stats["deposito"] == 2
    assert populated_stats["retiro"] == 0
    assert populated_stats["gestion_cuenta"] == 1


def test_contract_keyword_arguments_service_type():
    """Verify issue_ticket, peek_next, and call_next work with service_type keyword argument."""
    manager = BranchQueueManager()
    ticket = manager.issue_ticket(client_name="Alice", service_type="deposito")
    assert ticket.number == 1
    assert ticket.client_name == "Alice"
    assert ticket.service_type == ServiceType.DEPOSIT
    assert ticket.service_type.value == "deposito"

    peeked = manager.peek_next(service_type="deposito")
    assert peeked == ticket

    called = manager.call_next(service_type="deposito")
    assert called == ticket

    # Backward-compatible keyword argument 'service'
    ticket2 = manager.issue_ticket(client_name="Bob", service="retiro")
    assert ticket2.number == 2
    assert manager.peek_next(service="retiro") == ticket2
    assert manager.call_next(service="retiro") == ticket2

