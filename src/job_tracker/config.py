"""Application configuration loaded from environment variables."""

import os
from collections.abc import Mapping
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when required application configuration is missing."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings required by the job tracker."""

    aws_region: str
    table_name: str
    role_arn: str

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> "Settings":
        """Create settings from an environment-variable mapping."""
        values = os.environ if environment is None else environment

        required_names = (
            "AWS_REGION",
            "JOB_TRACKER_TABLE_NAME",
            "JOB_TRACKER_ROLE_ARN",
        )
        missing = [name for name in required_names if not values.get(name)]

        if missing:
            names = ", ".join(missing)
            raise ConfigurationError(f"Missing required environment variables: {names}")

        return cls(
            aws_region=values["AWS_REGION"],
            table_name=values["JOB_TRACKER_TABLE_NAME"],
            role_arn=values["JOB_TRACKER_ROLE_ARN"],
        )
