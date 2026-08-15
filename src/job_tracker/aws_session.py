"""Create an AWS session using temporary runtime-role credentials."""

from typing import Protocol, TypedDict

import boto3

from job_tracker.config import Settings


class TemporaryCredentials(TypedDict):
    """Credentials returned by AWS STS."""

    AccessKeyId: str
    SecretAccessKey: str
    SessionToken: str


class AssumeRoleResponse(TypedDict):
    """Relevant portion of the STS AssumeRole response."""

    Credentials: TemporaryCredentials


class StsClient(Protocol):
    """Interface required from an STS client."""

    def assume_role(
        self,
        *,
        RoleArn: str,
        RoleSessionName: str,
        DurationSeconds: int,
    ) -> AssumeRoleResponse:
        """Request temporary credentials for a role."""


def assume_runtime_role(
    settings: Settings,
    sts_client: StsClient | None = None,
) -> boto3.Session:
    """Assume the runtime role and return a session using temporary credentials."""
    client = sts_client or boto3.client("sts", region_name=settings.aws_region)

    response = client.assume_role(
        RoleArn=settings.role_arn,
        RoleSessionName="job-tracker-cli",
        DurationSeconds=3600,
    )
    credentials = response["Credentials"]

    return boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=settings.aws_region,
    )
