from unittest.mock import Mock, patch

from job_tracker.aws_session import assume_runtime_role
from job_tracker.config import Settings


def test_assume_runtime_role_creates_session_with_temporary_credentials() -> None:
    settings = Settings(
        aws_region="us-west-2",
        table_name="example-jobs",
        role_arn="arn:aws:iam::123456789012:role/example-runtime",
    )
    sts_client = Mock()
    sts_client.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "temporary-access-key",
            "SecretAccessKey": "temporary-secret-key",
            "SessionToken": "temporary-session-token",
        }
    }
    expected_session = object()

    with patch(
        "job_tracker.aws_session.boto3.Session",
        return_value=expected_session,
    ) as session_factory:
        session = assume_runtime_role(settings, sts_client=sts_client)

    sts_client.assume_role.assert_called_once_with(
        RoleArn=settings.role_arn,
        RoleSessionName="job-tracker-cli",
        DurationSeconds=3600,
    )
    session_factory.assert_called_once_with(
        aws_access_key_id="temporary-access-key",
        aws_secret_access_key="temporary-secret-key",
        aws_session_token="temporary-session-token",
        region_name="us-west-2",
    )
    assert session is expected_session
