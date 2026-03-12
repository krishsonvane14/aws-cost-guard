"""Tests for src.anomaly_engine — spend variance detection."""

from __future__ import annotations

import pytest

from src.anomaly_engine import analyze_spend_variance


class TestAnomalyEngine:
    """Verify anomaly detection across normal, edge, and extreme cases."""

    def test_no_anomaly_within_threshold(self) -> None:
        """Spend equal to the average should not trigger an anomaly."""
        result = analyze_spend_variance(10.0, 10.0)
        assert result.is_anomaly is False
        assert result.percentage_variance == pytest.approx(0.0, abs=0.01)

    def test_anomaly_detected_above_threshold(self) -> None:
        """A 50 % spike above the 7-day average must be flagged."""
        result = analyze_spend_variance(15.0, 10.0)
        assert result.is_anomaly is True
        assert result.percentage_variance == pytest.approx(50.0, abs=0.01)

    def test_exact_threshold_boundary_is_not_anomaly(self) -> None:
        """Exactly 20 % should NOT trigger — we use strictly greater than,
        not greater than or equal to."""
        result = analyze_spend_variance(12.0, 10.0)
        assert result.is_anomaly is False

    def test_spend_below_baseline_is_not_anomaly(self) -> None:
        """Spending less than the average is not an anomaly."""
        result = analyze_spend_variance(8.0, 10.0)
        assert result.is_anomaly is False

    def test_zero_rolling_average_does_not_raise(self) -> None:
        """Edge case — first day of month, no historical data."""
        result = analyze_spend_variance(5.0, 0.0)
        assert result is not None
        assert result.is_anomaly is False

    def test_large_spike_triggers_anomaly(self) -> None:
        """A 10x spike should clearly trigger an anomaly."""
        result = analyze_spend_variance(100.0, 10.0)
        assert result.is_anomaly is True
        assert result.percentage_variance == pytest.approx(900.0, abs=0.01)
