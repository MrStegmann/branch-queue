"""Exception hierarchy for Queue Manager."""

from src.exceptions.errors import (
    BranchQueueError,
    EmptyClientNameError,
    EmptyQueueError,
    InvalidServiceTypeError,
    QueueOperationError,
    ValidationError,
)

__all__ = [
    "BranchQueueError",
    "ValidationError",
    "InvalidServiceTypeError",
    "EmptyClientNameError",
    "QueueOperationError",
    "EmptyQueueError",
]
