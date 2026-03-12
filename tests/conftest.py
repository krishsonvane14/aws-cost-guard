"""Shared pytest fixtures for AWS Cost Guard tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def _set_test_env() -> None:
    """Inject required environment variables for the entire test session."""
    os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/test/fake"
    os.environ["SLACK_WEBHOOK_URL"] = "https://hooks.slack.com/services/test/fake"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
