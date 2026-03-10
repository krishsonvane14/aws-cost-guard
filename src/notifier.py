"""Webhook delivery — sends a JSON payload to Discord / Slack."""

from __future__ import annotations

from typing import Any

import requests


def send_webhook(webhook_url: str, payload: dict[str, Any]) -> None:
    """POST *payload* as JSON to *webhook_url*.

    Raises :class:`RuntimeError` with the HTTP status and response body
    when the request fails so the caller can log it.
    """
    resp = requests.post(
        webhook_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if not resp.ok:
        raise RuntimeError(
            f"Discord webhook request failed \u2014 HTTP {resp.status_code}: {resp.text}"
        )
