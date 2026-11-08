"""BranchQueueManager domain service coordinator."""

from collections import deque
from datetime import datetime, timezone
import threading
from typing import Callable, Optional, Union, List, Dict

from src.models.service_type import ServiceType
from src.models.ticket import Ticket
from src.models.stats import QueueStats
from src.exceptions.errors import EmptyClientNameError, EmptyQueueError, InvalidServiceTypeError


class BranchQueueManager:
    """
    Central operational coordinator managing isolated FIFO lines, monotonic ticket sequence,
    and thread synchronization for Banco Meridional.
    """

    def __init__(self, time_provider: Optional[Callable[[], datetime]] = None) -> None:
        """
        Initializes the BranchQueueManager with isolated deques for each ServiceType.

        Args:
            time_provider: Optional factory returning datetime instances. Defaults to timezone.utc now.
        """
        self._time_provider = time_provider or (lambda: datetime.now(timezone.utc))
        self._lock = threading.Lock()
        self._next_ticket_number: int = 1
        self._queues: dict[ServiceType, deque] = {
            ServiceType.DEPOSIT: deque(),
            ServiceType.WITHDRAWAL: deque(),
            ServiceType.ACCOUNT_MANAGEMENT: deque(),
        }

    def reset(self) -> None:
        """
        Clears all queues and resets the global ticket sequence number to 1.
        Thread-safe.
        """
        with self._lock:
            for q in self._queues.values():
                q.clear()
            self._next_ticket_number = 1

    def issue_ticket(
        self,
        client_name: str,
        service_type: Optional[Union[str, ServiceType]] = None,
        *,
        service: Optional[Union[str, ServiceType]] = None,
    ) -> Ticket:
        """
        Issues a new sequential ticket for a validated client and service type.

        Preconditions:
            - client_name is non-empty and contains non-whitespace characters.
            - service_type (or backward-compatible service) matches a valid ServiceType enum value or string representation.

        Postconditions:
            - Returned Ticket has a monotonic number incremented by exactly 1 from previous.
            - Ticket is appended to the corresponding ServiceType FIFO queue.
            - Counter is incremented only AFTER validation passes.

        Raises:
            EmptyClientNameError: If client_name is empty or whitespace only.
            InvalidServiceTypeError: If service_type is not provided or not a recognized ServiceType.

        Returns:
            Ticket: The newly created immutable Ticket instance.
        """
        raw_service = service_type if service_type is not None else service
        if raw_service is None:
            raise InvalidServiceTypeError("Service type is required.")

        # Pre-validation (Constitution: fail before advancing sequence)
        resolved_service = ServiceType.from_string(raw_service)
        if not isinstance(client_name, str) or not client_name.strip():
            raise EmptyClientNameError("Client name cannot be blank or whitespace-only.")

        with self._lock:
            ticket_number = self._next_ticket_number
            ticket = Ticket(
                number=ticket_number,
                client_name=client_name,
                service_type=resolved_service,
                issued_at=self._time_provider(),
            )
            self._queues[resolved_service].append(ticket)
            self._next_ticket_number += 1
            return ticket

    def call_next(
        self,
        service_type: Optional[Union[str, ServiceType]] = None,
        *,
        service: Optional[Union[str, ServiceType]] = None,
    ) -> Ticket:
        """
        Dispatches the longest-waiting client from the specified service queue.

        Preconditions:
            - service_type (or backward-compatible service) matches a valid ServiceType.

        Postconditions:
            - If queue is non-empty: The oldest ticket is removed from the queue and returned.
            - If queue is empty: Raises EmptyQueueError.
            - Queue depth for the service decrements by 1.
            - Other service queues remain completely unaffected.

        Raises:
            EmptyQueueError: If the queue for the specified service is empty.
            InvalidServiceTypeError: If service is missing or invalid.

        Returns:
            Ticket: The dispatched ticket.
        """
        raw_service = service_type if service_type is not None else service
        if raw_service is None:
            raise InvalidServiceTypeError("Service type is required.")

        resolved_service = ServiceType.from_string(raw_service)
        with self._lock:
            q = self._queues[resolved_service]
            if not q:
                raise EmptyQueueError(
                    f"No clients waiting for service '{resolved_service.value}'."
                )
            return q.popleft()

    def peek_next(
        self,
        service_type: Optional[Union[str, ServiceType]] = None,
        *,
        service: Optional[Union[str, ServiceType]] = None,
    ) -> Optional[Ticket]:
        """
        Inspects the next waiting client for the specified service WITHOUT mutating the queue.

        Preconditions:
            - service_type (or backward-compatible service) matches a valid ServiceType.

        Postconditions:
            - Queue order, depth, and contents remain 100% identical before and after the call.
            - Idempotent and thread-safe.

        Raises:
            InvalidServiceTypeError: If service is missing or invalid.

        Returns:
            Optional[Ticket]: The next ticket to be served, or None if the queue is empty.
        """
        raw_service = service_type if service_type is not None else service
        if raw_service is None:
            raise InvalidServiceTypeError("Service type is required.")

        resolved_service = ServiceType.from_string(raw_service)
        with self._lock:
            q = self._queues[resolved_service]
            if not q:
                return None
            return q[0]

    def list_waiting(
        self,
        service_type: Optional[Union[str, ServiceType]] = None,
        *,
        service: Optional[Union[str, ServiceType]] = None,
    ) -> Dict[str, List[Ticket]]:
        """
        Returns a dictionary organized by service containing currently waiting tickets.

        Args:
            service_type: If specified, returns a dictionary containing tickets only for that service category.
            service: Backward-compatible keyword alias for service_type.
            If neither is specified, returns a dictionary mapping each canonical Spanish service name to its list of waiting tickets.

        Postconditions:
            - Queue state is never mutated.
            - Returned lists are defensive copies.

        Raises:
            InvalidServiceTypeError: If service is provided but invalid.

        Returns:
            Dict[str, List[Ticket]]: Dictionary organized by service mapping to list of waiting tickets.
        """
        target = service_type if service_type is not None else service
        if target is not None:
            resolved_service = ServiceType.from_string(target)
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
        """
        Computes real-time queue depth metrics across all service lines including total count.

        Postconditions:
            - Computes instantaneous counts in O(1) time.
            - Queue state is untouched.

        Returns:
            Dict[str, int]: Dictionary mapping canonical Spanish service names and 'total' to their queue depths.
        """
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

    def get_stats(self) -> QueueStats:
        """
        Computes real-time queue depth metrics across all service lines.

        Postconditions:
            - Computes instantaneous counts in O(1) time.
            - Queue state is untouched.

        Returns:
            QueueStats: Object containing counts_by_service, total_waiting, and snapshot_time.
        """
        with self._lock:
            counts = {
                ServiceType.DEPOSIT: len(self._queues[ServiceType.DEPOSIT]),
                ServiceType.WITHDRAWAL: len(self._queues[ServiceType.WITHDRAWAL]),
                ServiceType.ACCOUNT_MANAGEMENT: len(
                    self._queues[ServiceType.ACCOUNT_MANAGEMENT]
                ),
            }
            total = sum(counts.values())
            return QueueStats(
                counts_by_service=counts,
                total_waiting=total,
                snapshot_time=self._time_provider(),
            )
