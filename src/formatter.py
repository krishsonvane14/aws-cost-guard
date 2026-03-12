"""Format a CostReport into a Discord-compatible webhook payload."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .models import CostData, CostReport

COLOR_RED = 16711680   # #FF0000
COLOR_GREEN = 65280    # #00FF00


def _usd(amount: float, currency: str) -> str:
    return f"${amount:.2f} {currency}"


def format_cost_payload(report: CostReport) -> dict[str, Any]:
    """Build a Discord embed payload from *report*."""
    cost_data = report.cost_data
    anomaly = report.anomaly_report

    description: str | None = None
    if anomaly.is_anomaly:
        sign = "+" if anomaly.percentage_variance > 0 else ""
        description = (
            f"**\u26a0\ufe0f Spend anomaly detected!** Yesterday\u2019s spend was "
            f"**{sign}{anomaly.percentage_variance}%** above the 7-day average."
        )

    if report.top_services:
        top_services_value = "\n".join(
            f"\u2022 **{s.service_name}**: {_usd(s.amount, cost_data.currency)}"
            for s in report.top_services
        )
    else:
        top_services_value = "No service data available."

    fields: list[dict[str, Any]] = [
        {
            "name": "\U0001f4b0 Yesterday Spend",
            "value": _usd(cost_data.yesterday_spend, cost_data.currency),
            "inline": True,
        },
        {
            "name": "\U0001f4c5 Month to Date",
            "value": _usd(cost_data.month_to_date_spend, cost_data.currency),
            "inline": True,
        },
        {
            "name": "\U0001f4ca 7-Day Average",
            "value": _usd(anomaly.seven_day_average, cost_data.currency),
            "inline": True,
        },
        {
            "name": "\U0001f3c6 Top Services",
            "value": top_services_value,
            "inline": False,
        },
    ]

    embed: dict[str, Any] = {
        "title": "AWS Daily Cost Report",
        "color": COLOR_RED if anomaly.is_anomaly else COLOR_GREEN,
        "fields": fields,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if description is not None:
        embed["description"] = description

    return {"embeds": [embed]}


def exceeds_threshold(cost_data: CostData, threshold_usd: float) -> bool:
    """Return ``True`` when MTD spend exceeds *threshold_usd*."""
    return cost_data.month_to_date_spend > threshold_usd
