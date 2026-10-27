"""Shared pytest fixtures and test configuration."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Generator
import pytest

# Ensure repository root is on sys.path for direct module imports
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def fixed_now() -> datetime:
    """Returns a deterministic reference datetime."""
    return datetime(2026, 10, 27, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_time_provider(fixed_now: datetime) -> Callable[[], datetime]:
    """Returns a time provider function that yields the fixed datetime."""
    return lambda: fixed_now


class SteppingTimeProvider:
    """Deterministic time provider that advances by a fixed interval on each call."""

    def __init__(self, start_time: datetime, step_seconds: float = 1.0) -> None:
        from datetime import timedelta
        self._current = start_time
        self._step = timedelta(seconds=step_seconds)

    def __call__(self) -> datetime:
        now = self._current
        self._current += self._step
        return now


@pytest.fixture
def stepping_time_provider(fixed_now: datetime) -> SteppingTimeProvider:
    """Fixture providing a clock that advances 1 second on each call."""
    return SteppingTimeProvider(fixed_now)
