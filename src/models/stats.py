"""QueueStats domain model representing instantaneous branch queue metrics."""

from dataclasses import dataclass
from datetime import datetime
from src.models.service_type import ServiceType


@dataclass(frozen=True)
class QueueStats:
    """
    Immutable snapshot of real-time queue metrics across the branch.
    """

    counts_by_service: dict[ServiceType, int]
    total_waiting: int
    snapshot_time: datetime
