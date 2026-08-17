import json
from unittest.mock import Mock, patch

import pytest

from job_tracker.cli import main
from job_tracker.config import Settings
from job_tracker.domain import JobStatus
from job_tracker.repository import JobRepository


def example_settings() -> Settings:
    return Settings(
        aws_region="us-west-2",
        table_name="example-jobs",
        role_arn="arn:aws:iam::123456789012:role/example-runtime",
    )


def test_main_creates_job(capsys: pytest.CaptureFixture[str]) -> None:
    repository = Mock(spec=JobRepository)
    repository.create_job.return_value = {
        "job_id": "job-123",
        "status": "QUEUED",
    }

    with (
        patch(
            "job_tracker.cli.Settings.from_environment",
            return_value=example_settings(),
        ),
        patch(
            "job_tracker.cli.create_repository",
            return_value=repository,
        ),
    ):
        exit_code = main(
            [
                "create",
                "--team-id",
                "platform",
                "--job-type",
                "deployment",
            ]
        )

    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["job_id"] == "job-123"
    repository.create_job.assert_called_once_with("platform", "deployment")


def test_main_reports_missing_job(
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = Mock(spec=JobRepository)
    repository.get_job.return_value = None

    with (
        patch(
            "job_tracker.cli.Settings.from_environment",
            return_value=example_settings(),
        ),
        patch(
            "job_tracker.cli.create_repository",
            return_value=repository,
        ),
    ):
        exit_code = main(["get", "missing-job"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Job not found" in captured.err


def test_main_converts_status_arguments() -> None:
    repository = Mock(spec=JobRepository)
    repository.update_status.return_value = {
        "job_id": "job-123",
        "status": "RUNNING",
    }

    with (
        patch(
            "job_tracker.cli.Settings.from_environment",
            return_value=example_settings(),
        ),
        patch(
            "job_tracker.cli.create_repository",
            return_value=repository,
        ),
    ):
        exit_code = main(
            [
                "update",
                "job-123",
                "--current-status",
                "QUEUED",
                "--new-status",
                "RUNNING",
            ]
        )

    assert exit_code == 0
    repository.update_status.assert_called_once_with(
        "job-123",
        JobStatus.QUEUED,
        JobStatus.RUNNING,
        error_code=None,
        error_message=None,
    )
