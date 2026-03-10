import type { CostEntry, WebhookPayload } from "./types.js";

export function formatCostPayload(entry: CostEntry): WebhookPayload {
  const topServices = [...entry.services]
    .sort((a, b) => parseFloat(b.amount) - parseFloat(a.amount))
    .slice(0, 10);

  const totalFormatted = parseFloat(entry.totalAmount).toFixed(2);
  const period = `${entry.timePeriod.start} → ${entry.timePeriod.end}`;

  return {
    title: `AWS Cost Report: $${totalFormatted} ${entry.unit}`,
    period,
    totalCost: totalFormatted,
    currency: entry.unit,
    services: topServices,
    timestamp: new Date().toISOString(),
  };
}

export function exceedsThreshold(
  entry: CostEntry,
  thresholdUsd: number
): boolean {
  return parseFloat(entry.totalAmount) > thresholdUsd;
}
