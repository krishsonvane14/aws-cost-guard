"""AWS Cost Guard — entry point, config loading, and orchestration."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from .anomaly_engine import analyze_spend_variance
from .aws_client import AWSCostClient
from .formatter import exceeds_threshold, format_cost_payload
from .models import CostData, CostReport
from .notifier import send_webhook


def _load_config() -> dict[str, str | float]:
    """Read and validate environment variables."""
    load_dotenv()

    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        raise SystemExit("Missing required env var: WEBHOOK_URL")

    return {
        "aws_region": os.environ.get("AWS_REGION", "us-east-1"),
        "webhook_url": webhook_url,
        "cost_threshold": float(os.environ.get("COST_THRESHOLD_USD", "100")),
    }


def main() -> None:
    config = _load_config()
    client = AWSCostClient(region=str(config["aws_region"]))

    print("Fetching AWS cost data\u2026")

    partial = client.get_yesterday_and_mtd()
    top_services = client.get_top_services()
    seven_day_avg = client.get_seven_day_average()

    cost_data = CostData(
        yesterday_spend=partial["yesterday_spend"],
        month_to_date_spend=partial["month_to_date_spend"],
        forecasted_spend=0.0,
        currency=partial["currency"],
    )

    anomaly_report = analyze_spend_variance(cost_data.yesterday_spend, seven_day_avg)

    print(
        f"MTD: ${cost_data.month_to_date_spend:.2f} | "
        f"Yesterday: ${cost_data.yesterday_spend:.2f} | "
        f"7-day avg: ${seven_day_avg:.2f}"
    )

    threshold = float(config["cost_threshold"])
    if not exceeds_threshold(cost_data, threshold):
        print(
            f"MTD spend ${cost_data.month_to_date_spend:.2f} is within "
            f"threshold ${threshold:.0f}. No alert sent."
        )
        return

    report = CostReport(
        cost_data=cost_data,
        top_services=top_services,
        anomaly_report=anomaly_report,
    )

    payload = format_cost_payload(report)
    send_webhook(str(config["webhook_url"]), payload)
    print(
        f"Alert sent \u2014 anomaly: {anomaly_report.is_anomaly}, "
        f"variance: {anomaly_report.percentage_variance}%"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        sys.exit(1)
