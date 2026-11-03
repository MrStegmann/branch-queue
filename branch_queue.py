"""Banco Meridional Branch Queue Manager root module.

Exports primary classes, enumerations, exceptions, and models for root-level access.
"""

from src.models.service_type import ServiceType
from src.models.ticket import Ticket, TicketStatus
from src.models.stats import QueueStats
from src.exceptions.errors import (
    BranchQueueError,
    ValidationError,
    InvalidServiceTypeError,
    EmptyClientNameError,
    QueueOperationError,
    EmptyQueueError,
)
from src.services.queue_manager import BranchQueueManager
from src.cli.terminal import main

__all__ = [
    "BranchQueueManager",
    "ServiceType",
    "Ticket",
    "TicketStatus",
    "QueueStats",
    "BranchQueueError",
    "ValidationError",
    "InvalidServiceTypeError",
    "EmptyClientNameError",
    "QueueOperationError",
    "EmptyQueueError",
    "main",
]

if __name__ == "__main__":
    main()

