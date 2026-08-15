from datetime import UTC, datetime

import pytest

from job_tracker.domain import (
    InvalidStatusTransition,
    JobStatus,
    calculate_expiration,
    validate_status_transition,
)


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (JobStatus.QUEUED, JobStatus.RUNNING),
        (JobStatus.QUEUED, JobStatus.FAILED),
        (JobStatus.RUNNING, JobStatus.SUCCEEDED),
        (JobStatus.RUNNING, JobStatus.FAILED),
    ],
)
def test_valid_status_transitions(
    current_status: JobStatus,
    new_status: JobStatus,
) -> None:
    validate_status_transition(current_status, new_status)


def test_terminal_status_cannot_transition() -> None:
    with pytest.raises(InvalidStatusTransition):
        validate_status_transition(JobStatus.SUCCEEDED, JobStatus.RUNNING)


def test_calculate_expiration() -> None:
    created_at = datetime(2026, 8, 15, tzinfo=UTC)

    expiration = calculate_expiration(created_at, retention_days=30)

    expected = int(datetime(2026, 9, 14, tzinfo=UTC).timestamp())
    assert expiration == expected


def test_expiration_requires_timezone() -> None:
    naive_datetime = datetime(2026, 8, 15, tzinfo=UTC).replace(tzinfo=None)

    with pytest.raises(ValueError, match="timezone"):
        calculate_expiration(naive_datetime, retention_days=30)
