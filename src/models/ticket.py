"""Ticket domain model and TicketStatus enumeration."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.exceptions.errors import EmptyClientNameError, ValidationError
from src.models.service_type import ServiceType


class TicketStatus(str, Enum):
    """Lifecycle statuses for a customer ticket."""

    ISSUED = "ISSUED"
    WAITING = "WAITING"
    SERVING = "SERVING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Ticket:
    """
    Immutable domain record representing a customer's queue position and service request.
    """

    number: int
    client_name: str
    service_type: ServiceType
    issued_at: datetime

    def __post_init__(self) -> None:
        # Validate ticket number
        if not isinstance(self.number, int) or self.number <= 0:
            raise ValidationError(
                f"Ticket number must be a strictly positive integer (> 0). Got: {self.number}"
            )

        # Validate and normalize client_name
        if not isinstance(self.client_name, str):
            raise EmptyClientNameError("Client name must be a non-empty string.")

        trimmed_name = self.client_name.strip()
        if not trimmed_name:
            raise EmptyClientNameError("Client name cannot be blank or whitespace-only.")

        # Mutate frozen dataclass field cleanly during post-init
        object.__setattr__(self, "client_name", trimmed_name)

        # Ensure service_type is normalized
        if not isinstance(self.service_type, ServiceType):
            resolved_service = ServiceType.from_string(self.service_type)
            object.__setattr__(self, "service_type", resolved_service)

        # Validate issued_at
        if not isinstance(self.issued_at, datetime):
            raise ValidationError(f"issued_at must be a datetime instance. Got: {type(self.issued_at).__name__}")
