"""Integration tests for multi-threaded concurrency and race condition prevention."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from src.models.service_type import ServiceType
from src.services.queue_manager import BranchQueueManager


def test_concurrent_ticket_issuance_uniqueness():
    """Verify that hundreds of concurrent ticket requests generate strictly unique sequence numbers."""
    manager = BranchQueueManager()
    total_tickets = 300
    issued_tickets = []
    lock = threading.Lock()

    def worker(i: int):
        services = [ServiceType.DEPOSIT, ServiceType.WITHDRAWAL, ServiceType.ACCOUNT_MANAGEMENT]
        chosen_service = services[i % len(services)]
        ticket = manager.issue_ticket(f"Client-{i}", chosen_service)
        with lock:
            issued_tickets.append(ticket)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(total_tickets)]
        for f in as_completed(futures):
            f.result()

    assert len(issued_tickets) == total_tickets
    numbers = [t.number for t in issued_tickets]
    assert len(set(numbers)) == total_tickets
    assert min(numbers) == 1
    assert max(numbers) == total_tickets


def test_concurrent_dispatch_no_double_servicing():
    """Verify that multiple concurrent tellers calling next never receive duplicate tickets."""
    manager = BranchQueueManager()
    tickets_to_issue = 150
    for i in range(tickets_to_issue):
        manager.issue_ticket(f"Client-{i}", ServiceType.DEPOSIT)

    dispatched = []
    lock = threading.Lock()

    def teller_worker():
        while True:
            t = manager.call_next(ServiceType.DEPOSIT)
            if t is None:
                break
            with lock:
                dispatched.append(t)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(teller_worker) for _ in range(8)]
        for f in as_completed(futures):
            f.result()

    assert len(dispatched) == tickets_to_issue
    dispatched_numbers = [t.number for t in dispatched]
    # No duplicate tickets served
    assert len(set(dispatched_numbers)) == tickets_to_issue
    # Queue is now completely empty
    assert manager.call_next(ServiceType.DEPOSIT) is None
