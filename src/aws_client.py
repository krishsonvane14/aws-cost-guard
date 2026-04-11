"""AWS Cost Explorer client — fetches spend data via boto3."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from .models import ServiceCost


def _parse_amount(raw: str | None) -> float:
    """Safely parse a Cost Explorer amount string to float."""
    try:
        return float(raw or "0")
    except (ValueError, TypeError):
        return 0.0


def _iso(d: date) -> str:
    return d.isoformat()


class AWSCostClient:
    """Thin wrapper around the Cost Explorer GetCostAndUsage API."""

    def __init__(self, region: str = "us-east-1") -> None:
        self._client = boto3.client("ce", region_name=region)

    def get_yesterday_and_mtd(self) -> dict[str, Any]:
        """Return yesterday's spend, MTD total, and currency."""
        today = datetime.now(UTC).date()
        yesterday = today - timedelta(days=1)
        month_start = today.replace(day=1)

        try:
            yd_resp = self._get_cost(yesterday, today, "DAILY")

            if month_start == today:
                # First of month: MTD is just yesterday's spend (last month's last day)
                mtd_spend = _parse_amount(
                    (yd_resp.get("ResultsByTime") or [{}])[0]
                    .get("Total", {})
                    .get("UnblendedCost", {})
                    .get("Amount")
                )
            else:
                mtd_resp = self._get_cost(month_start, today, "DAILY")
                mtd_spend = sum(
                    _parse_amount((r.get("Total") or {}).get("UnblendedCost", {}).get("Amount"))
                    for r in mtd_resp.get("ResultsByTime", [])
                )
        except NoCredentialsError as e:
            raise RuntimeError(
                "AWS credentials not configured. Verify the OIDC role is set up correctly."
            ) from e
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("AccessDeniedException", "DataUnavailableException"):
                raise PermissionError(
                    f"IAM role missing ce:GetCostAndUsage permission or data not yet available: {e}"
                ) from e
            raise RuntimeError(f"AWS API error [{error_code}]: {e}") from e

        yd_result = (yd_resp.get("ResultsByTime") or [{}])[0]
        yd_total = (yd_result.get("Total") or {}).get("UnblendedCost") or {}
        currency = yd_total.get("Unit", "USD")

        return {
            "yesterday_spend": _parse_amount(yd_total.get("Amount")),
            "month_to_date_spend": mtd_spend,
            "currency": currency,
        }

    def get_top_services(self, limit: int = 5) -> list[ServiceCost]:
        """Fetch the top services for the current month."""
        today = datetime.now(UTC).date()
        month_start = today.replace(day=1)

        if month_start == today:
            # First of month: fall back to last month's data
            last_month_end = today - timedelta(days=1)  # e.g. March 31
            month_start = last_month_end.replace(day=1)  # e.g. March 1
            end = today  # April 1 (exclusive → covers all of March)
        else:
            end = today

        try:
            resp = self._get_cost(
                month_start,
                end,
                "MONTHLY",
                group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )
        except NoCredentialsError as e:
            raise RuntimeError(
                "AWS credentials not configured. Verify the OIDC role is set up correctly."
            ) from e
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            raise RuntimeError(f"AWS API error [{error_code}]: {e}") from e

        groups = (resp.get("ResultsByTime") or [{}])[0].get("Groups", [])
        services = [
            ServiceCost(
                service_name=(g.get("Keys") or ["Unknown"])[0],
                amount=_parse_amount(
                    (g.get("Metrics") or {}).get("UnblendedCost", {}).get("Amount")
                ),
            )
            for g in groups
        ]
        services.sort(key=lambda s: s.amount, reverse=True)
        return services[:limit]

    def get_seven_day_average(self) -> float:
        """Return the arithmetic mean of daily spend over the last 7 days."""
        today = datetime.now(UTC).date()
        start = today - timedelta(days=7)

        try:
            resp = self._get_cost(start, today, "DAILY")
        except NoCredentialsError as e:
            raise RuntimeError(
                "AWS credentials not configured. Verify the OIDC role is set up correctly."
            ) from e
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            # DataUnavailableException can occur on the 1st of the month
            if error_code == "DataUnavailableException":
                return 0.0
            raise RuntimeError(f"AWS API error [{error_code}]: {e}") from e

        days = resp.get("ResultsByTime", [])
        if not days:
            return 0.0

        total = sum(
            _parse_amount((r.get("Total") or {}).get("UnblendedCost", {}).get("Amount"))
            for r in days
        )
        return total / len(days)

    def _get_cost(
        self,
        start: date,
        end: date,
        granularity: str,
        *,
        group_by: list[dict[str, str]] | None = None,
    ) -> Any:
        # Guard: Cost Explorer requires start to be strictly before end.
        # Return an empty result instead of hitting the API with an invalid range.
        if start >= end:
            return {"ResultsByTime": []}

        kwargs: dict[str, Any] = {
            "TimePeriod": {"Start": _iso(start), "End": _iso(end)},
            "Granularity": granularity,
            "Metrics": ["UnblendedCost"],
        }
        if group_by:
            kwargs["GroupBy"] = group_by
        return self._client.get_cost_and_usage(**kwargs)
