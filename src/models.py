"""Data models for the AWS Cost Guard project."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CostData:
    """Aggregated spend figures for a single reporting window."""

    yesterday_spend: float
    """Total spend for the previous calendar day, in *currency* units."""

    month_to_date_spend: float
    """Accumulated spend from the first of the current month to today."""

    forecasted_spend: float
    """AWS Cost Explorer end-of-month forecast (0 until implemented)."""

    currency: str = "USD"
    """ISO 4217 currency code."""


@dataclass(frozen=True)
class ServiceCost:
    """Cost breakdown for a single AWS service."""

    service_name: str
    """Human-readable AWS service name (e.g. ``Amazon EC2``)."""

    amount: float
    """Unblended cost for the service in the reporting period."""


@dataclass(frozen=True)
class AnomalyReport:
    """Anomaly detection result derived from recent spend history."""

    is_anomaly: bool
    """``True`` when current spend deviates beyond the acceptable threshold."""

    seven_day_average: float
    """Rolling average of daily spend over the past 7 days."""

    percentage_variance: float
    """How much yesterday's spend differs from the 7-day average (e.g. 42.5 = +42.5 %)."""


@dataclass(frozen=True)
class CostReport:
    """Top-level report produced by a single Cost Guard run."""

    cost_data: CostData
    """High-level spend figures (yesterday, MTD, forecast)."""

    top_services: list[ServiceCost] = field(default_factory=list)
    """The top 5 AWS services by spend for the reporting period."""

    anomaly_report: AnomalyReport = field(
        default_factory=lambda: AnomalyReport(
            is_anomaly=False, seven_day_average=0.0, percentage_variance=0.0
        )
    )
    """Anomaly detection summary for the current period."""
