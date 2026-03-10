import type { CostData, CostReport, DiscordEmbedField, WebhookPayload } from "./types.js";

const COLOR_RED = 16711680;   // #FF0000
const COLOR_GREEN = 65280;    // #00FF00

function usd(amount: number, currency: string): string {
  return `$${amount.toFixed(2)} ${currency}`;
}

export function formatCostPayload(report: CostReport): WebhookPayload {
  const { costData, topServices, anomalyReport } = report;
  const { isAnomaly, sevenDayAverage, percentageVariance } = anomalyReport;

  const description = isAnomaly
    ? `**⚠️ Spend anomaly detected!** Yesterday's spend was **${percentageVariance > 0 ? "+" : ""}${percentageVariance}%** above the 7-day average.`
    : undefined;

  const topServicesValue =
    topServices.length > 0
      ? topServices
          .map((s) => `• **${s.serviceName}**: ${usd(s.amount, costData.currency)}`)
          .join("\n")
      : "No service data available.";

  const fields: DiscordEmbedField[] = [
    {
      name: "💰 Yesterday Spend",
      value: usd(costData.yesterdaySpend, costData.currency),
      inline: true,
    },
    {
      name: "📅 Month to Date",
      value: usd(costData.monthToDateSpend, costData.currency),
      inline: true,
    },
    {
      name: "📊 7-Day Average",
      value: usd(sevenDayAverage, costData.currency),
      inline: true,
    },
    {
      name: "🏆 Top Services",
      value: topServicesValue,
      inline: false,
    },
  ];

  return {
    embeds: [
      {
        title: "AWS Daily Cost Report",
        ...(description !== undefined ? { description } : {}),
        color: isAnomaly ? COLOR_RED : COLOR_GREEN,
        fields,
        timestamp: new Date().toISOString(),
      },
    ],
  };
}

export function exceedsThreshold(
  costData: CostData,
  thresholdUsd: number
): boolean {
  return costData.monthToDateSpend > thresholdUsd;
}
