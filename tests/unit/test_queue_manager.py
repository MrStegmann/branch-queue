"""Unit tests for BranchQueueManager."""

from datetime import datetime
import pytest

from src.services.queue_manager import BranchQueueManager
from src.models.service_type import ServiceType
from src.exceptions.errors import EmptyClientNameError, EmptyQueueError, InvalidServiceTypeError


# --- Phase 3 / US1 Tests ---

def test_issue_ticket_monotonic_sequence(mock_time_provider, fixed_now: datetime):
    manager = BranchQueueManager(time_provider=mock_time_provider)

    t1 = manager.issue_ticket("Alice", ServiceType.DEPOSIT)
    t2 = manager.issue_ticket("Bob", ServiceType.WITHDRAWAL)
    t3 = manager.issue_ticket("Charlie", ServiceType.ACCOUNT_MANAGEMENT)
    t4 = manager.issue_ticket("Diana", ServiceType.DEPOSIT)

    assert t1.number == 1
    assert t1.client_name == "Alice"
    assert t1.service_type == ServiceType.DEPOSIT
    assert t1.issued_at == fixed_now

    assert t2.number == 2
    assert t2.client_name == "Bob"
    assert t2.service_type == ServiceType.WITHDRAWAL

    assert t3.number == 3
    assert t3.client_name == "Charlie"
    assert t3.service_type == ServiceType.ACCOUNT_MANAGEMENT

    assert t4.number == 4
    assert t4.client_name == "Diana"
    assert t4.service_type == ServiceType.DEPOSIT


def test_issue_ticket_accepts_service_strings(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)

    t1 = manager.issue_ticket("Alice", "deposit")
    t2 = manager.issue_ticket("Bob", "WITHDRAWAL")
    t3 = manager.issue_ticket("Charlie", "account management")
    t4 = manager.issue_ticket("Dave", "1")

    assert t1.service_type == ServiceType.DEPOSIT
    assert t2.service_type == ServiceType.WITHDRAWAL
    assert t3.service_type == ServiceType.ACCOUNT_MANAGEMENT
    assert t4.service_type == ServiceType.DEPOSIT


def test_issue_ticket_whitespace_trimmed(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    t = manager.issue_ticket("   Eve Smith   ", "deposit")
    assert t.client_name == "Eve Smith"


def test_issue_ticket_invalid_client_name_does_not_advance_counter(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)

    t1 = manager.issue_ticket("Alice", "deposit")
    assert t1.number == 1

    with pytest.raises(EmptyClientNameError):
        manager.issue_ticket("", "deposit")

    with pytest.raises(EmptyClientNameError):
        manager.issue_ticket("    ", "deposit")

    # Counter must not have advanced!
    t2 = manager.issue_ticket("Bob", "withdrawal")
    assert t2.number == 2


def test_issue_ticket_invalid_service_does_not_advance_counter(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)

    t1 = manager.issue_ticket("Alice", "deposit")
    assert t1.number == 1

    with pytest.raises(InvalidServiceTypeError):
        manager.issue_ticket("Bob", "crypto_trading")

    # Counter must not have advanced!
    t2 = manager.issue_ticket("Charlie", "account_management")
    assert t2.number == 2


def test_reset_clears_queue_and_resets_sequence(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    manager.issue_ticket("Alice", "deposit")
    manager.issue_ticket("Bob", "withdrawal")

    manager.reset()

    # Next ticket should be #1 again
    t_new = manager.issue_ticket("Charlie", "deposit")
    assert t_new.number == 1


# --- Phase 4 / US2 Tests ---

def test_call_next_fifo_order(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    t1 = manager.issue_ticket("Alice", ServiceType.DEPOSIT)
    t2 = manager.issue_ticket("Bob", ServiceType.DEPOSIT)
    t3 = manager.issue_ticket("Charlie", ServiceType.DEPOSIT)

    # First call_next should return Alice (longest waiting)
    called1 = manager.call_next(ServiceType.DEPOSIT)
    assert called1 == t1
    assert called1.client_name == "Alice"
    assert called1.number == 1

    # Second call_next should return Bob
    called2 = manager.call_next(ServiceType.DEPOSIT)
    assert called2 == t2
    assert called2.client_name == "Bob"

    # Third call_next should return Charlie
    called3 = manager.call_next(ServiceType.DEPOSIT)
    assert called3 == t3

    # Empty queue raises EmptyQueueError
    with pytest.raises(EmptyQueueError):
        manager.call_next(ServiceType.DEPOSIT)


def test_call_next_queue_isolation(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    t_dep = manager.issue_ticket("Alice", ServiceType.DEPOSIT)
    t_wd = manager.issue_ticket("Bob", ServiceType.WITHDRAWAL)
    t_acct = manager.issue_ticket("Charlie", ServiceType.ACCOUNT_MANAGEMENT)

    # Calling withdrawal should only dequeue Bob
    called_wd = manager.call_next(ServiceType.WITHDRAWAL)
    assert called_wd == t_wd

    # Calling withdrawal again should raise EmptyQueueError
    with pytest.raises(EmptyQueueError):
        manager.call_next(ServiceType.WITHDRAWAL)

    # Deposit and Account Management are untouched
    assert manager.call_next(ServiceType.DEPOSIT) == t_dep
    assert manager.call_next(ServiceType.ACCOUNT_MANAGEMENT) == t_acct


def test_call_next_empty_queue_raises_error(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    with pytest.raises(EmptyQueueError):
        manager.call_next(ServiceType.DEPOSIT)
    with pytest.raises(EmptyQueueError):
        manager.call_next("withdrawal")
    with pytest.raises(EmptyQueueError):
        manager.call_next("account_management")


def test_call_next_invalid_service_raises_error(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    with pytest.raises(InvalidServiceTypeError):
        manager.call_next("invalid_service")


# --- Phase 5 / US3 Tests ---

def test_peek_next_non_mutating(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    t1 = manager.issue_ticket("Alice", ServiceType.DEPOSIT)
    t2 = manager.issue_ticket("Bob", ServiceType.DEPOSIT)

    # Peek multiple times
    peeked1 = manager.peek_next(ServiceType.DEPOSIT)
    peeked2 = manager.peek_next(ServiceType.DEPOSIT)

    assert peeked1 == t1
    assert peeked2 == t1
    assert peeked1.number == 1
    assert peeked1.client_name == "Alice"

    # Verify queue was not mutated: call_next still yields Alice first, then Bob
    assert manager.call_next(ServiceType.DEPOSIT) == t1
    assert manager.call_next(ServiceType.DEPOSIT) == t2
    with pytest.raises(EmptyQueueError):
        manager.call_next(ServiceType.DEPOSIT)


def test_peek_next_empty_queue_returns_none(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    assert manager.peek_next(ServiceType.DEPOSIT) is None
    assert manager.peek_next("withdrawal") is None
    assert manager.peek_next("account_management") is None


def test_peek_next_invalid_service_raises_error(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    with pytest.raises(InvalidServiceTypeError):
        manager.peek_next("invalid_service")


def test_list_waiting_specific_service(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    t1 = manager.issue_ticket("Alice", ServiceType.DEPOSIT)
    manager.issue_ticket("Bob", ServiceType.WITHDRAWAL)
    t3 = manager.issue_ticket("Charlie", ServiceType.DEPOSIT)

    deposit_dict = manager.list_waiting(ServiceType.DEPOSIT)
    assert deposit_dict == {"deposito": [t1, t3]}

    # Modifying returned list does not affect internal queue
    deposit_dict["deposito"].pop()
    assert len(manager.list_waiting(ServiceType.DEPOSIT)["deposito"]) == 2


def test_list_waiting_all_services(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    t1 = manager.issue_ticket("Alice", ServiceType.DEPOSIT)
    t2 = manager.issue_ticket("Bob", ServiceType.WITHDRAWAL)
    t3 = manager.issue_ticket("Charlie", ServiceType.DEPOSIT)
    t4 = manager.issue_ticket("Diana", ServiceType.ACCOUNT_MANAGEMENT)

    all_waiting = manager.list_waiting()
    assert all_waiting == {
        "deposito": [t1, t3],
        "retiro": [t2],
        "gestion_cuenta": [t4],
    }

    # Verify empty dict returned when queues are empty
    empty_manager = BranchQueueManager(time_provider=mock_time_provider)
    assert empty_manager.list_waiting() == {
        "deposito": [],
        "retiro": [],
        "gestion_cuenta": [],
    }
    assert empty_manager.list_waiting(ServiceType.DEPOSIT) == {"deposito": []}


def test_list_waiting_invalid_service_raises_error(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    with pytest.raises(InvalidServiceTypeError):
        manager.list_waiting("invalid_service")


# --- Phase 6 / US4 Tests ---

def test_get_stats_empty_queues(mock_time_provider, fixed_now: datetime):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    stats = manager.get_stats()

    assert stats.total_waiting == 0
    assert stats.counts_by_service[ServiceType.DEPOSIT] == 0
    assert stats.counts_by_service[ServiceType.WITHDRAWAL] == 0
    assert stats.counts_by_service[ServiceType.ACCOUNT_MANAGEMENT] == 0
    assert stats.snapshot_time == fixed_now


def test_get_stats_populated_queues(mock_time_provider, fixed_now: datetime):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    manager.issue_ticket("Alice", ServiceType.DEPOSIT)
    manager.issue_ticket("Bob", ServiceType.DEPOSIT)
    manager.issue_ticket("Charlie", ServiceType.WITHDRAWAL)

    stats = manager.get_stats()

    assert stats.total_waiting == 3
    assert stats.counts_by_service[ServiceType.DEPOSIT] == 2
    assert stats.counts_by_service[ServiceType.WITHDRAWAL] == 1
    assert stats.counts_by_service[ServiceType.ACCOUNT_MANAGEMENT] == 0
    assert stats.snapshot_time == fixed_now

    # Dequeue one deposit ticket and verify stats update immediately
    manager.call_next(ServiceType.DEPOSIT)
    updated_stats = manager.get_stats()
    assert updated_stats.total_waiting == 2
    assert updated_stats.counts_by_service[ServiceType.DEPOSIT] == 1


def test_stats_method_with_total_and_services(mock_time_provider):
    manager = BranchQueueManager(time_provider=mock_time_provider)
    assert manager.stats() == {
        "deposito": 0,
        "retiro": 0,
        "gestion_cuenta": 0,
        "total": 0,
    }

    manager.issue_ticket("Alice", "deposit")
    manager.issue_ticket("Bob", "deposit")
    manager.issue_ticket("Charlie", "withdrawal")

    assert manager.stats() == {
        "deposito": 2,
        "retiro": 1,
        "gestion_cuenta": 0,
        "total": 3,
    }

    # Calling next decrements specific service and total count
    manager.call_next("deposit")
    assert manager.stats() == {
        "deposito": 1,
        "retiro": 1,
        "gestion_cuenta": 0,
        "total": 2,
    }


def test_service_type_keyword_arguments(mock_time_provider):
    """Test that service_type keyword arguments are supported across all public manager methods."""
    manager = BranchQueueManager(time_provider=mock_time_provider)

    t1 = manager.issue_ticket(client_name="Alice", service_type="deposito")
    assert t1.number == 1
    assert t1.service_type == ServiceType.DEPOSIT

    t2 = manager.issue_ticket(client_name="Bob", service_type=ServiceType.WITHDRAWAL)
    assert t2.number == 2
    assert t2.service_type == ServiceType.WITHDRAWAL

    # peek_next with keyword
    assert manager.peek_next(service_type="deposito") == t1
    assert manager.peek_next(service_type=ServiceType.WITHDRAWAL) == t2

    # list_waiting with keyword
    assert manager.list_waiting(service_type="deposito") == {"deposito": [t1]}
    assert manager.list_waiting(service_type=ServiceType.WITHDRAWAL) == {"retiro": [t2]}

    # call_next with keyword
    assert manager.call_next(service_type="deposito") == t1
    assert manager.call_next(service_type=ServiceType.WITHDRAWAL) == t2
    with pytest.raises(EmptyQueueError):
        manager.call_next(service_type="deposito")




