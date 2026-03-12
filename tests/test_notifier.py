"""Tests for src.notifier — webhook delivery."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests.exceptions

from src.notifier import send_webhook

FAKE_WEBHOOK_URL = "https://discord.com/api/webhooks/test/fake"

DUMMY_PAYLOAD = {
    "embeds": [
        {
            "title": "AWS Daily Cost Report",
            "color": 16711680,
            "fields": [
                {"name": "Yesterday Spend", "value": "$85.00 USD", "inline": True},
            ],
            "description": (
                "**⚠️ Spend anomaly detected!** "
                "Yesterday's spend was **+45%** above the 7-day average."
            ),
        }
    ]
}


class TestNotifier:
    """Verify webhook delivery and error handling."""

    @patch("src.notifier.requests.post")
    def test_send_alert_called_with_correct_url(self, mock_post: MagicMock) -> None:
        """requests.post must be called exactly once with the webhook URL."""
        mock_post.return_value = MagicMock(status_code=204, ok=True)
        mock_post.return_value.raise_for_status = MagicMock()

        send_webhook(FAKE_WEBHOOK_URL, DUMMY_PAYLOAD)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == FAKE_WEBHOOK_URL

    @patch("src.notifier.requests.post")
    def test_alert_includes_anomaly_percentage(self, mock_post: MagicMock) -> None:
        """The JSON body sent to Discord must contain the anomaly percentage."""
        mock_post.return_value = MagicMock(status_code=204, ok=True)
        mock_post.return_value.raise_for_status = MagicMock()

        send_webhook(FAKE_WEBHOOK_URL, DUMMY_PAYLOAD)

        call_kwargs = mock_post.call_args
        payload_sent = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        payload_str = str(payload_sent)
        assert "45" in payload_str

    @patch("src.notifier.requests.post")
    def test_connection_error_raises_runtime_error(self, mock_post: MagicMock) -> None:
        """A ConnectionError from requests must surface as RuntimeError."""
        mock_post.side_effect = requests.exceptions.ConnectionError("refused")

        with pytest.raises(RuntimeError, match="(?i)connect"):
            send_webhook(FAKE_WEBHOOK_URL, DUMMY_PAYLOAD)

    @patch("src.notifier.requests.post")
    def test_timeout_raises_runtime_error(self, mock_post: MagicMock) -> None:
        """A Timeout from requests must surface as RuntimeError."""
        mock_post.side_effect = requests.exceptions.Timeout("timed out")

        with pytest.raises(RuntimeError):
            send_webhook(FAKE_WEBHOOK_URL, DUMMY_PAYLOAD)
