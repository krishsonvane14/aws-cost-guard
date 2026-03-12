"""Tests for src.aws_client — Cost Explorer wrapper."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from botocore.exceptions import NoCredentialsError
from moto import mock_aws

from src.aws_client import AWSCostClient


class TestAWSClient:
    """Verify AWSCostClient handles real and failing AWS responses."""

    @mock_aws
    def test_fetch_cost_data_returns_correct_shape(self) -> None:
        """Under moto, get_yesterday_and_mtd should return a dict with
        the expected keys and sane default values."""
        # NEEDS IMPLEMENTATION REVIEW: moto's Cost Explorer support is
        # limited — it may return empty results. We verify the method
        # runs without error and returns the correct structure.
        client = AWSCostClient(region="us-east-1")
        result = client.get_yesterday_and_mtd()

        assert "yesterday_spend" in result
        assert isinstance(result["yesterday_spend"], float)
        assert result["yesterday_spend"] >= 0

    @mock_aws
    def test_fetch_seven_day_average_returns_float(self) -> None:
        """get_seven_day_average should return a non-negative float."""
        client = AWSCostClient(region="us-east-1")
        avg = client.get_seven_day_average()

        assert isinstance(avg, float)
        assert avg >= 0.0

    def test_fetch_cost_data_no_credentials_raises(self) -> None:
        """When AWS credentials are missing, a RuntimeError must be raised
        with the word 'credentials' in the message."""
        with patch("boto3.client") as mock_client:
            mock_client.return_value.get_cost_and_usage.side_effect = (
                NoCredentialsError()
            )
            client = AWSCostClient(region="us-east-1")
            # Replace the internal client with our mock
            client._client = mock_client.return_value

            with pytest.raises(RuntimeError, match="(?i)credentials"):
                client.get_yesterday_and_mtd()

    @mock_aws
    def test_fetch_handles_empty_result_set(self) -> None:
        """moto returns $0 for new accounts — the function must handle
        this gracefully without raising."""
        client = AWSCostClient(region="us-east-1")
        top = client.get_top_services(limit=5)

        # Empty or zero-cost services are acceptable, but no exception.
        assert isinstance(top, list)
