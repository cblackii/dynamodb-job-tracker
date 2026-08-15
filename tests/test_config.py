import pytest

from job_tracker.config import ConfigurationError, Settings


def test_settings_load_from_environment() -> None:
    environment = {
        "AWS_REGION": "us-west-2",
        "JOB_TRACKER_TABLE_NAME": "example-jobs",
        "JOB_TRACKER_ROLE_ARN": "arn:aws:iam::123456789012:role/example-runtime",
    }

    settings = Settings.from_environment(environment)

    assert settings.aws_region == "us-west-2"
    assert settings.table_name == "example-jobs"
    assert settings.role_arn.endswith("example-runtime")


def test_settings_reject_missing_values() -> None:
    with pytest.raises(ConfigurationError, match="JOB_TRACKER_ROLE_ARN"):
        Settings.from_environment(
            {
                "AWS_REGION": "us-west-2",
                "JOB_TRACKER_TABLE_NAME": "example-jobs",
            }
        )
