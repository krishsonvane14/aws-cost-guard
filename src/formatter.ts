import type { CostData, ServiceCost, WebhookPayload } from "./types.js";

export function formatCostPayload(
  costData: CostData,
  topServices: ServiceCost[]
): WebhookPayload {
  const totalFormatted = costData.monthToDateSpend.toFixed(2);

  return {
    title: `AWS Cost Report (MTD): $${totalFormatted} ${costData.currency}`,
    period: `MTD · yesterday $${costData.yesterdaySpend.toFixed(2)}`,
    totalCost: totalFormatted,
    currency: costData.currency,
    services: topServices,
    timestamp: new Date().toISOString(),
  };
}

export function exceedsThreshold(
  costData: CostData,
  thresholdUsd: number
): boolean {
  return costData.monthToDateSpend > thresholdUsd;
}
