from datetime import UTC, datetime
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from botocore.exceptions import ClientError

from job_tracker.domain import InvalidStatusTransition, JobStatus
from job_tracker.repository import JobRepository, StatusConflictError


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


def test_update_status_uses_expected_status_condition() -> None:
    table = Mock()
    now = datetime(2026, 8, 15, 12, 30, tzinfo=UTC)
    updated_item = {
        "job_id": "job-123",
        "status": "RUNNING",
        "updated_at": "2026-08-15T12:30:00Z",
    }
    table.update_item.return_value = {"Attributes": updated_item}
    repository = JobRepository(table, clock=lambda: now)

    result = repository.update_status(
        "job-123",
        JobStatus.QUEUED,
        JobStatus.RUNNING,
    )

    assert result == updated_item
    table.update_item.assert_called_once_with(
        Key={"job_id": "job-123"},
        UpdateExpression="SET #status = :new_status, updated_at = :updated_at",
        ConditionExpression=(
            "attribute_exists(job_id) AND #status = :expected_status"
        ),
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":new_status": JobStatus.RUNNING,
            ":updated_at": "2026-08-15T12:30:00Z",
            ":expected_status": JobStatus.QUEUED,
        },
        ReturnValues="ALL_NEW",
    )


def test_update_status_rejects_invalid_transition() -> None:
    table = Mock()
    repository = JobRepository(table)

    with pytest.raises(InvalidStatusTransition):
        repository.update_status(
            "job-123",
            JobStatus.SUCCEEDED,
            JobStatus.RUNNING,
        )

    table.update_item.assert_not_called()


def test_update_status_reports_concurrent_change() -> None:
    table = Mock()
    table.update_item.side_effect = ClientError(
        {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "Condition failed",
            }
        },
        "UpdateItem",
    )
    repository = JobRepository(table)

    with pytest.raises(StatusConflictError, match="concurrently"):
        repository.update_status(
            "job-123",
            JobStatus.QUEUED,
            JobStatus.RUNNING,
        )
