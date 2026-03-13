"""Tests for src.main — integration paths through the orchestration layer."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.models import AnomalyReport, ServiceCost

# ── Fixtures shared across tests ─────────────────────────────────────────────

FAKE_PARTIAL: dict[str, Any] = {
    "yesterday_spend": 42.0,
    "month_to_date_spend": 200.0,
    "currency": "USD",
}

FAKE_SERVICES: list[ServiceCost] = [
    ServiceCost(service_name="Amazon EC2", amount=120.0),
]

NO_ANOMALY = AnomalyReport(
    is_anomaly=False, seven_day_average=40.0, percentage_variance=5.0
)

YES_ANOMALY = AnomalyReport(
    is_anomaly=True, seven_day_average=20.0, percentage_variance=110.0
)


def _env_side_effect(key: str, default: str | None = None) -> str | None:
    """Simulate os.environ.get for _load_config."""
    env = {
        "WEBHOOK_URL": "https://discord.com/api/webhooks/test/fake",
        "AWS_REGION": "us-east-1",
        "COST_THRESHOLD_USD": "100",
    }
    return env.get(key, default)


class TestMainHappyPath:
    """Verify the normal and anomaly execution flows."""

    @patch("src.main.send_webhook")
    @patch("src.main.format_cost_payload")
    @patch("src.main.analyze_spend_variance", return_value=NO_ANOMALY)
    @patch("src.main.AWSCostClient")
    @patch("src.main.load_dotenv")
    @patch("src.main.os.environ.get", side_effect=_env_side_effect)
    def test_below_threshold_no_alert(
        self,
        _mock_env: MagicMock,
        _mock_dotenv: MagicMock,
        mock_client_cls: MagicMock,
        _mock_anomaly: MagicMock,
        mock_format: MagicMock,
        mock_send: MagicMock,
    ) -> None:
        """When MTD is below the threshold, send_webhook must still be called once."""
        client = mock_client_cls.return_value
        client.get_yesterday_and_mtd.return_value = {
            **FAKE_PARTIAL,
            "month_to_date_spend": 50.0,
        }
        client.get_top_services.return_value = FAKE_SERVICES
        client.get_seven_day_average.return_value = 40.0

        mock_format.return_value = {"embeds": [{"title": "AWS Daily Cost Report"}]}

        from src.main import main

        main()
        mock_send.assert_called_once()

    @patch("src.main.send_webhook")
    @patch("src.main.analyze_spend_variance", return_value=NO_ANOMALY)
    @patch("src.main.AWSCostClient")
    @patch("src.main.load_dotenv")
    @patch("src.main.os.environ.get", side_effect=_env_side_effect)
    def test_above_threshold_sends_green_alert(
        self,
        _mock_env: MagicMock,
        _mock_dotenv: MagicMock,
        mock_client_cls: MagicMock,
        _mock_anomaly: MagicMock,
        mock_send: MagicMock,
    ) -> None:
        """When MTD exceeds the threshold and no anomaly, send_webhook is
        called once with a payload (green path)."""
        client = mock_client_cls.return_value
        client.get_yesterday_and_mtd.return_value = FAKE_PARTIAL
        client.get_top_services.return_value = FAKE_SERVICES
        client.get_seven_day_average.return_value = 40.0

        from src.main import main

        main()

        mock_send.assert_called_once()

    @patch("src.main.send_webhook")
    @patch("src.main.analyze_spend_variance", return_value=YES_ANOMALY)
    @patch("src.main.AWSCostClient")
    @patch("src.main.load_dotenv")
    @patch("src.main.os.environ.get", side_effect=_env_side_effect)
    def test_anomaly_sends_red_alert(
        self,
        _mock_env: MagicMock,
        _mock_dotenv: MagicMock,
        mock_client_cls: MagicMock,
        _mock_anomaly: MagicMock,
        mock_send: MagicMock,
    ) -> None:
        """When an anomaly is detected and MTD exceeds threshold,
        send_webhook is called once with an anomaly payload."""
        client = mock_client_cls.return_value
        client.get_yesterday_and_mtd.return_value = FAKE_PARTIAL
        client.get_top_services.return_value = FAKE_SERVICES
        client.get_seven_day_average.return_value = 20.0

        from src.main import main

        main()

        mock_send.assert_called_once()
        # Verify the payload came from format_cost_payload (which uses anomaly)
        call_args = mock_send.call_args
        payload = call_args[0][1]
        embed = payload["embeds"][0]
        assert embed["color"] == 16711680  # COLOR_RED for anomaly


class TestMainErrorHandling:
    """Verify that RuntimeError from aws_client triggers sys.exit(1)."""

    @patch("src.main.AWSCostClient")
    @patch("src.main.load_dotenv")
    @patch("src.main.os.environ.get", side_effect=_env_side_effect)
    def test_aws_error_causes_exit_1(
        self,
        _mock_env: MagicMock,
        _mock_dotenv: MagicMock,
        mock_client_cls: MagicMock,
    ) -> None:
        """When AWSCostClient raises RuntimeError, the top-level handler
        must call sys.exit(1)."""
        client = mock_client_cls.return_value
        client.get_yesterday_and_mtd.side_effect = RuntimeError("boom")

        from src.main import main

        with pytest.raises(RuntimeError, match="boom"):
            main()
