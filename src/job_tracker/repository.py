"""DynamoDB persistence operations for automation jobs."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol, cast
from uuid import uuid4

from job_tracker.domain import JobStatus, calculate_expiration

JobItem = dict[str, str | int]


class DynamoDBTable(Protocol):
    """DynamoDB table operations required by this repository."""

    def put_item(self, **kwargs: Any) -> dict[str, Any]:
        """Store an item."""

    def get_item(self, **kwargs: Any) -> dict[str, Any]:
        """Retrieve an item."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


class JobRepository:
    """Store and retrieve automation jobs in DynamoDB."""

    def __init__(
        self,
        table: DynamoDBTable,
        *,
        retention_days: int = 30,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._table = table
        self._retention_days = retention_days
        self._clock = clock

    def create_job(self, team_id: str, job_type: str) -> JobItem:
        """Create a queued job with a generated identifier and TTL."""
        if not team_id.strip():
            raise ValueError("team_id cannot be empty")

        if not job_type.strip():
            raise ValueError("job_type cannot be empty")

        now = self._clock()
        timestamp = (
            now.astimezone(UTC)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )

        item: JobItem = {
            "job_id": str(uuid4()),
            "team_id": team_id.strip(),
            "job_type": job_type.strip(),
            "status": JobStatus.QUEUED,
            "created_at": timestamp,
            "updated_at": timestamp,
            "expires_at": calculate_expiration(now, self._retention_days),
        }

        self._table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(job_id)",
        )
        return item

    def get_job(self, job_id: str) -> JobItem | None:
        """Retrieve one job by its partition key."""
        if not job_id.strip():
            raise ValueError("job_id cannot be empty")

        response = self._table.get_item(
            Key={"job_id": job_id.strip()},
            ConsistentRead=True,
        )
        item = response.get("Item")

        if item is None:
            return None

        return cast(JobItem, item)
