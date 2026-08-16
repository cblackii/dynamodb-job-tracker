from datetime import UTC, datetime
from unittest.mock import Mock, patch
from uuid import UUID

from job_tracker.domain import JobStatus
from job_tracker.repository import JobRepository


def test_create_job_stores_queued_record() -> None:
    table = Mock()
    now = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)
    repository = JobRepository(table, clock=lambda: now)
    job_uuid = UUID("12345678-1234-5678-1234-567812345678")

    with patch("job_tracker.repository.uuid4", return_value=job_uuid):
        item = repository.create_job("platform", "infrastructure-deployment")

    assert item["job_id"] == str(job_uuid)
    assert item["status"] == JobStatus.QUEUED
    assert item["created_at"] == "2026-08-15T12:00:00Z"
    assert item["updated_at"] == item["created_at"]
    assert item["expires_at"] == 1789387200
    table.put_item.assert_called_once_with(
        Item=item,
        ConditionExpression="attribute_not_exists(job_id)",
    )


def test_get_job_returns_stored_item() -> None:
    stored_item = {
        "job_id": "job-123",
        "team_id": "platform",
        "job_type": "security-scan",
        "status": "QUEUED",
        "created_at": "2026-08-15T12:00:00Z",
        "updated_at": "2026-08-15T12:00:00Z",
        "expires_at": 1789387200,
    }
    table = Mock()
    table.get_item.return_value = {"Item": stored_item}
    repository = JobRepository(table)

    result = repository.get_job("job-123")

    assert result == stored_item
    table.get_item.assert_called_once_with(
        Key={"job_id": "job-123"},
        ConsistentRead=True,
    )


def test_get_job_returns_none_when_missing() -> None:
    table = Mock()
    table.get_item.return_value = {}
    repository = JobRepository(table)

    assert repository.get_job("missing-job") is None
