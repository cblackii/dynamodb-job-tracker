"""Business rules for automation jobs."""

from datetime import datetime, timedelta
from enum import StrEnum


class JobStatus(StrEnum):
    """Supported job lifecycle states."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class InvalidStatusTransition(ValueError):
    """Raised when a job cannot move to the requested status."""


ALLOWED_TRANSITIONS = {
    JobStatus.QUEUED: frozenset({JobStatus.RUNNING, JobStatus.FAILED}),
    JobStatus.RUNNING: frozenset({JobStatus.SUCCEEDED, JobStatus.FAILED}),
    JobStatus.SUCCEEDED: frozenset(),
    JobStatus.FAILED: frozenset(),
}


def validate_status_transition(
    current_status: JobStatus,
    new_status: JobStatus,
) -> None:
    """Reject status changes that violate the job lifecycle."""
    if new_status not in ALLOWED_TRANSITIONS[current_status]:
        raise InvalidStatusTransition(
            f"Cannot transition from {current_status} to {new_status}"
        )


def calculate_expiration(
    created_at: datetime,
    retention_days: int,
) -> int:
    """Return a Unix timestamp used by DynamoDB TTL."""
    if created_at.tzinfo is None or created_at.utcoffset() is None:
        raise ValueError("created_at must include timezone information")

    if retention_days <= 0:
        raise ValueError("retention_days must be greater than zero")

    return int((created_at + timedelta(days=retention_days)).timestamp())
