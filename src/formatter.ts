import type { WebhookPayload } from "./types.js";
import type { CostEntry } from "./aws-client.js";

export function formatCostPayload(entry: CostEntry): WebhookPayload {
  const topServices = [...entry.services]
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 10);

  const totalFormatted = entry.totalAmount.toFixed(2);
  const period = `${entry.timePeriod.start} → ${entry.timePeriod.end}`;

  return {
    title: `AWS Cost Report: $${totalFormatted} ${entry.currency}`,
    period,
    totalCost: totalFormatted,
    currency: entry.currency,
    services: topServices,
    timestamp: new Date().toISOString(),
  };
}

export function exceedsThreshold(
  entry: CostEntry,
  thresholdUsd: number
): boolean {
  return entry.totalAmount > thresholdUsd;
}
