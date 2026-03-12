"""Webhook delivery — sends a JSON payload to Discord / Slack."""

from __future__ import annotations

from typing import Any

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout


def send_webhook(webhook_url: str, payload: dict[str, Any]) -> None:
    """POST *payload* as JSON to *webhook_url*.

    Raises :class:`RuntimeError` with the HTTP status and response body
    when the request fails so the caller can log it.
    """
    try:
        resp = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
    except Timeout as e:
        raise RuntimeError(f"Webhook request timed out after 10s: {e}") from e
    except ConnectionError as e:
        raise RuntimeError(f"Failed to connect to webhook URL: {e}") from e
    except HTTPError as e:
        raise RuntimeError(
            f"Webhook returned HTTP {e.response.status_code}: {e}"
        ) from e
