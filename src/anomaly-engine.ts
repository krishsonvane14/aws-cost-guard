import type { AnomalyReport } from "./types.js";

/**
 * Compares `yesterdaySpend` against the rolling `sevenDayAverage` to
 * determine whether yesterday's spend constitutes a cost anomaly.
 *
 * @param yesterdaySpend - Total spend for the previous calendar day.
 * @param sevenDayAverage - Arithmetic mean of daily spend over the last 7 days.
 * @returns An {@link AnomalyReport} with variance rounded to 2 decimal places.
 *          `isAnomaly` is `true` when variance strictly exceeds 20 %.
 */
export function analyzeSpendVariance(
  yesterdaySpend: number,
  sevenDayAverage: number
): AnomalyReport {
  if (sevenDayAverage === 0) {
    return { isAnomaly: false, sevenDayAverage: 0, percentageVariance: 0 };
  }

  const rawVariance = ((yesterdaySpend - sevenDayAverage) / sevenDayAverage) * 100;
  const percentageVariance = Math.round(rawVariance * 100) / 100;

  return {
    isAnomaly: percentageVariance > 20,
    sevenDayAverage,
    percentageVariance,
  };
}
