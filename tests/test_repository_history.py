from unittest.mock import Mock, patch

import pytest

from job_tracker.repository import JobRepository


def test_list_recent_jobs_queries_team_index_newest_first() -> None:
    jobs = [{"job_id": "job-2"}, {"job_id": "job-1"}]
    table = Mock()
    table.query.return_value = {"Items": jobs}
    repository = JobRepository(table)
    condition = object()

    with patch("job_tracker.repository.Key") as key:
        key.return_value.eq.return_value = condition
        result = repository.list_recent_jobs("platform", limit=10)

    assert result == jobs
    key.assert_called_once_with("team_id")
    key.return_value.eq.assert_called_once_with("platform")
    table.query.assert_called_once_with(
        IndexName="TeamJobsIndex",
        KeyConditionExpression=condition,
        ScanIndexForward=False,
        Limit=10,
    )


def test_list_recent_jobs_rejects_invalid_limit() -> None:
    repository = JobRepository(Mock())

    with pytest.raises(ValueError, match="between 1 and 100"):
        repository.list_recent_jobs("platform", limit=0)


def test_delete_job_returns_deleted_item() -> None:
    deleted_item = {"job_id": "job-123", "status": "SUCCEEDED"}
    table = Mock()
    table.delete_item.return_value = {"Attributes": deleted_item}
    repository = JobRepository(table)

    result = repository.delete_job("job-123")

    assert result == deleted_item
    table.delete_item.assert_called_once_with(
        Key={"job_id": "job-123"},
        ReturnValues="ALL_OLD",
    )
