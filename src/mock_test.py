"""Mock integration test — exercises the full pipeline with static fixtures.

Usage:
    cp .env.example .env   # set a real WEBHOOK_URL first
    python -m src.mock_test
"""

from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv

from .anomaly_engine import analyze_spend_variance
from .formatter import format_cost_payload
from .models import CostData, CostReport, ServiceCost
from .notifier import send_webhook

# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_COST_DATA = CostData(
    yesterday_spend=85.00,
    month_to_date_spend=450.00,
    forecasted_spend=0.0,
    currency="USD",
)

MOCK_TOP_SERVICES = [
    ServiceCost(service_name="Amazon EC2", amount=310.50),
    ServiceCost(service_name="Amazon RDS", amount=98.75),
    ServiceCost(service_name="Amazon S3", amount=40.75),
]

# At $20 average, yesterday's $85 is +325 % → well above the 20 % threshold.
MOCK_SEVEN_DAY_AVERAGE = 20.00


# ── Orchestration ─────────────────────────────────────────────────────────────

def main() -> None:
    load_dotenv()

    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        raise SystemExit("Missing required env var: WEBHOOK_URL")

    print("=== AWS Cost Guard — Mock Test ===\n")
    print(f"Yesterday spend : ${MOCK_COST_DATA.yesterday_spend:.2f}")
    print(f"Month to date   : ${MOCK_COST_DATA.month_to_date_spend:.2f}")
    print(f"7-day average   : ${MOCK_SEVEN_DAY_AVERAGE:.2f}")
    print(f"Top services    : {', '.join(s.service_name for s in MOCK_TOP_SERVICES)}\n")

    anomaly_report = analyze_spend_variance(
        MOCK_COST_DATA.yesterday_spend,
        MOCK_SEVEN_DAY_AVERAGE,
    )

    print(f"Anomaly detected : {anomaly_report.is_anomaly}")
    print(f"Variance         : {anomaly_report.percentage_variance}%\n")

    report = CostReport(
        cost_data=MOCK_COST_DATA,
        top_services=MOCK_TOP_SERVICES,
        anomaly_report=anomaly_report,
    )

    payload = format_cost_payload(report)
    print("Formatted Discord embed:")
    print(json.dumps(payload, indent=2))
    print()

    print(f"Sending webhook to: {webhook_url}")
    send_webhook(webhook_url, payload)
    print("Webhook sent successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Mock test failed: {exc}", file=sys.stderr)
        sys.exit(1)
