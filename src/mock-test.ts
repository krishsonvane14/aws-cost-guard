/**
 * Mock integration test — runs the full Cost Guard pipeline using static
 * fixtures instead of live AWS credentials.
 *
 * Usage:
 *   cp .env.example .env   # set a real WEBHOOK_URL first
 *   npm run dev -- src/mock-test.ts
 */
import "dotenv/config";
import { analyzeSpendVariance } from "./anomaly-engine.js";
import { formatCostPayload } from "./formatter.js";
import { sendWebhook } from "./notifier.js";
import type { CostData, CostReport, ServiceCost } from "./types.js";

// ── Fixtures ─────────────────────────────────────────────────────────────────

const mockCostData: CostData = {
  yesterdaySpend: 85.0,
  monthToDateSpend: 450.0,
  forecastedSpend: 0,
  currency: "USD",
};

const mockTopServices: ServiceCost[] = [
  { serviceName: "Amazon EC2", amount: 310.5 },
  { serviceName: "Amazon RDS", amount: 98.75 },
  { serviceName: "Amazon S3", amount: 40.75 },
];

/** At $20 average, yesterday's $85 is +325% → well above the 20% threshold. */
const MOCK_SEVEN_DAY_AVERAGE = 20.0;

// ── Orchestration ─────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const webhookUrl = process.env["WEBHOOK_URL"];
  if (!webhookUrl) {
    throw new Error("Missing required env var: WEBHOOK_URL");
  }

  console.log("=== AWS Cost Guard — Mock Test ===\n");
  console.log(`Yesterday spend : $${mockCostData.yesterdaySpend.toFixed(2)}`);
  console.log(`Month to date   : $${mockCostData.monthToDateSpend.toFixed(2)}`);
  console.log(`7-day average   : $${MOCK_SEVEN_DAY_AVERAGE.toFixed(2)}`);
  console.log(`Top services    : ${mockTopServices.map((s) => s.serviceName).join(", ")}\n`);

  const anomalyReport = analyzeSpendVariance(
    mockCostData.yesterdaySpend,
    MOCK_SEVEN_DAY_AVERAGE
  );

  console.log(`Anomaly detected : ${anomalyReport.isAnomaly}`);
  console.log(`Variance         : ${anomalyReport.percentageVariance}%\n`);

  const report: CostReport = {
    costData: mockCostData,
    topServices: mockTopServices,
    anomalyReport,
  };

  const payload = formatCostPayload(report);
  console.log("Formatted Discord embed:");
  console.log(JSON.stringify(payload, null, 2));
  console.log();

  console.log(`Sending webhook to: ${webhookUrl}`);
  await sendWebhook(webhookUrl, payload);
  console.log("Webhook sent successfully.");
}

main().catch((err: unknown) => {
  console.error("Mock test failed:", err);
  process.exit(1);
});
