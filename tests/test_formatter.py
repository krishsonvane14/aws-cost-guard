"""Tests for src.formatter — Discord/Slack payload construction."""

from __future__ import annotations

from src.formatter import COLOR_GREEN, COLOR_RED, exceeds_threshold, format_cost_payload
from src.models import AnomalyReport, CostData, CostReport, ServiceCost


def _make_report(*, is_anomaly: bool, pct: float = 0.0) -> CostReport:
    """Build a CostReport with the given anomaly state."""
    return CostReport(
        cost_data=CostData(
            yesterday_spend=42.57,
            month_to_date_spend=310.99,
            forecasted_spend=0.0,
            currency="USD",
        ),
        top_services=[
            ServiceCost(service_name="Amazon EC2", amount=180.25),
            ServiceCost(service_name="Amazon S3", amount=45.10),
        ],
        anomaly_report=AnomalyReport(
            is_anomaly=is_anomaly,
            seven_day_average=35.00,
            percentage_variance=pct,
        ),
    )


class TestFormatCostPayload:
    """Verify the Discord embed structure and conditional formatting."""

    def test_normal_payload_has_green_color(self) -> None:
        """A non-anomaly report must use COLOR_GREEN."""
        report = _make_report(is_anomaly=False, pct=5.0)
        payload = format_cost_payload(report)
        embed = payload["embeds"][0]
        assert embed["color"] == COLOR_GREEN

    def test_anomaly_payload_has_red_color(self) -> None:
        """An anomaly report must use COLOR_RED."""
        report = _make_report(is_anomaly=True, pct=50.0)
        payload = format_cost_payload(report)
        embed = payload["embeds"][0]
        assert embed["color"] == COLOR_RED

    def test_payload_contains_required_discord_keys(self) -> None:
        """The payload must have the top-level 'embeds' key, and each embed
        must contain 'title', 'color', and 'fields'."""
        report = _make_report(is_anomaly=False)
        payload = format_cost_payload(report)

        assert "embeds" in payload
        embed = payload["embeds"][0]
        assert "title" in embed
        assert "color" in embed
        assert "fields" in embed

    def test_dollar_amounts_have_two_decimal_places(self) -> None:
        """All dollar values in the fields must be formatted as $X.XX."""
        report = _make_report(is_anomaly=False, pct=0.0)
        payload = format_cost_payload(report)
        fields = payload["embeds"][0]["fields"]

        yesterday_field = fields[0]
        assert "$42.57" in yesterday_field["value"]

        mtd_field = fields[1]
        assert "$310.99" in mtd_field["value"]

    def test_positive_variance_renders_in_description(self) -> None:
        """A positive percentage_variance on an anomaly must appear in the
        embed description with a + prefix."""
        report = _make_report(is_anomaly=True, pct=25.0)
        payload = format_cost_payload(report)
        embed = payload["embeds"][0]

        assert "description" in embed
        assert "+25.0%" in embed["description"]


class TestExceedsThreshold:
    """Verify the threshold comparison helper."""

    def test_below_threshold_returns_false(self) -> None:
        """MTD below the threshold should not trigger."""
        cost_data = CostData(
            yesterday_spend=10.0,
            month_to_date_spend=50.0,
            forecasted_spend=0.0,
        )
        assert exceeds_threshold(cost_data, 100.0) is False

    def test_above_threshold_returns_true(self) -> None:
        """MTD above the threshold must trigger."""
        cost_data = CostData(
            yesterday_spend=10.0,
            month_to_date_spend=150.0,
            forecasted_spend=0.0,
        )
        assert exceeds_threshold(cost_data, 100.0) is True
