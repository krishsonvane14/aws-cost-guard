"""Anomaly detection — compares yesterday's spend to the 7-day average."""

from __future__ import annotations

from .models import AnomalyReport


def analyze_spend_variance(
    yesterday_spend: float,
    seven_day_average: float,
) -> AnomalyReport:
    """Return an :class:`AnomalyReport` based on the spend delta.

    * If *seven_day_average* is 0 the variance is reported as 0 % and
      ``is_anomaly`` is ``False`` (avoids division-by-zero).
    * ``is_anomaly`` is ``True`` when the percentage variance **strictly
      exceeds** 20 %.
    * The variance is rounded to 2 decimal places.
    """
    if seven_day_average == 0:
        return AnomalyReport(
            is_anomaly=False,
            seven_day_average=0.0,
            percentage_variance=0.0,
        )

    raw_variance = ((yesterday_spend - seven_day_average) / seven_day_average) * 100
    percentage_variance = round(raw_variance, 2)

    return AnomalyReport(
        is_anomaly=percentage_variance > 20,
        seven_day_average=seven_day_average,
        percentage_variance=percentage_variance,
    )
