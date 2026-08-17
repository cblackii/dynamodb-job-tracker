"""Command-line interface for the Cloud Automation Job Tracker."""

import argparse
import json
import sys
from collections.abc import Sequence
from decimal import Decimal

from botocore.exceptions import ClientError

from job_tracker.aws_session import assume_runtime_role
from job_tracker.config import Settings
from job_tracker.domain import JobStatus
from job_tracker.repository import (
    JobItem,
    JobRepository,
    StatusConflictError,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Track cloud automation jobs in DynamoDB."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="Create a queued job.")
    create.add_argument("--team-id", required=True)
    create.add_argument("--job-type", required=True)

    get = commands.add_parser("get", help="Retrieve one job.")
    get.add_argument("job_id")

    update = commands.add_parser("update", help="Update a job's status.")
    update.add_argument("job_id")
    update.add_argument(
        "--current-status",
        required=True,
        type=JobStatus,
        choices=list(JobStatus),
    )
    update.add_argument(
        "--new-status",
        required=True,
        type=JobStatus,
        choices=list(JobStatus),
    )
    update.add_argument("--error-code")
    update.add_argument("--error-message")

    history = commands.add_parser("list", help="List a team's recent jobs.")
    history.add_argument("--team-id", required=True)
    history.add_argument("--limit", type=int, default=20)

    delete = commands.add_parser("delete", help="Delete one job.")
    delete.add_argument("job_id")

    return parser


def create_repository(settings: Settings) -> JobRepository:
    """Create a repository using the least-privilege runtime role."""
    session = assume_runtime_role(settings)
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table(settings.table_name)
    return JobRepository(table)


def execute_command(
    arguments: argparse.Namespace,
    repository: JobRepository,
) -> JobItem | list[JobItem] | None:
    """Execute the selected repository operation."""
    if arguments.command == "create":
        return repository.create_job(arguments.team_id, arguments.job_type)

    if arguments.command == "get":
        return repository.get_job(arguments.job_id)

    if arguments.command == "update":
        return repository.update_status(
            arguments.job_id,
            arguments.current_status,
            arguments.new_status,
            error_code=arguments.error_code,
            error_message=arguments.error_message,
        )

    if arguments.command == "list":
        return repository.list_recent_jobs(
            arguments.team_id,
            limit=arguments.limit,
        )

    if arguments.command == "delete":
        return repository.delete_job(arguments.job_id)

    raise ValueError(f"Unsupported command: {arguments.command}")


def json_default(value: object) -> int | float:
    """Convert DynamoDB Decimal values into JSON-compatible numbers."""
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)

        return float(value)

    raise TypeError(f"Cannot serialize value of type {type(value).__name__}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line application."""
    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        settings = Settings.from_environment()
        repository = create_repository(settings)
        result = execute_command(arguments, repository)
    except (ClientError, StatusConflictError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if result is None:
        print("Job not found.", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, default=json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
