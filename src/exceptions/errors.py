"""Domain exceptions for Banco Meridional Queue Manager."""


class BranchQueueError(Exception):
    """Base exception for all queue operations in Banco Meridional."""
    pass


class ValidationError(BranchQueueError):
    """Raised when domain entity input or parameters fail validation."""
    pass


class InvalidServiceTypeError(ValidationError):
    """Raised when a provided service type string or value cannot be resolved."""
    pass


class EmptyClientNameError(ValidationError):
    """Raised when client name is empty, whitespace-only, or invalid."""
    pass


class QueueOperationError(BranchQueueError):
    """Raised when an illegal or failing queue operation occurs."""
    pass
