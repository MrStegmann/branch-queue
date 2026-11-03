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
    """English canonical service keys: deposit, withdrawal, account_management."""
    assert ServiceType.DEPOSIT.value == "deposit"
    assert ServiceType.WITHDRAWAL.value == "withdrawal"
    assert ServiceType.ACCOUNT_MANAGEMENT.value == "account_management"


def test_contract_call_next_raises_empty_queue_error():
    """call_next() must raise an error if the queue is empty."""
    manager = BranchQueueManager()
    with pytest.raises(EmptyQueueError) as exc_info:
        manager.call_next("deposit")
    assert "No clients waiting" in str(exc_info.value)

    with pytest.raises(EmptyQueueError):
        manager.call_next(ServiceType.WITHDRAWAL)

    with pytest.raises(EmptyQueueError):
        manager.call_next("account_management")


def test_contract_list_waiting_returns_dict_by_service():
    """list_waiting() must return a dictionary organized by service."""
    manager = BranchQueueManager()
    t1 = manager.issue_ticket("Alice", "deposit")
    t2 = manager.issue_ticket("Bob", "withdrawal")

    waiting = manager.list_waiting()
    assert isinstance(waiting, dict)
    assert set(waiting.keys()) == {"deposit", "withdrawal", "account_management"}
    assert waiting["deposit"] == [t1]
    assert waiting["withdrawal"] == [t2]
    assert waiting["account_management"] == []


def test_contract_stats_includes_total_count():
    """stats() must return a dictionary and include a 'total' count."""
    manager = BranchQueueManager()
    empty_stats = manager.stats()
    assert isinstance(empty_stats, dict)
    assert empty_stats == {
        "deposit": 0,
        "withdrawal": 0,
        "account_management": 0,
        "total": 0,
    }

    manager.issue_ticket("Alice", "deposit")
    manager.issue_ticket("Bob", "deposit")
    manager.issue_ticket("Charlie", "account_management")

    populated_stats = manager.stats()
    assert isinstance(populated_stats, dict)
    assert populated_stats["total"] == 3
    assert populated_stats["deposit"] == 2
    assert populated_stats["withdrawal"] == 0
    assert populated_stats["account_management"] == 1

