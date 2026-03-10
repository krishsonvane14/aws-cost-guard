import "dotenv/config";
import { analyzeSpendVariance } from "./anomaly-engine.js";
import { AWSCostClient } from "./aws-client.js";
import { exceedsThreshold, formatCostPayload } from "./formatter.js";
import { sendWebhook } from "./notifier.js";
import type { AppConfig, CostData } from "./types.js";

function loadConfig(): AppConfig {
  const required = ["WEBHOOK_URL"];
  for (const key of required) {
    if (!process.env[key]) throw new Error(`Missing required env var: ${key}`);
  }

  return {
    awsRegion: process.env["AWS_REGION"] ?? "us-east-1",
    webhookUrl: process.env["WEBHOOK_URL"] as string,
    costThreshold: parseFloat(process.env["COST_THRESHOLD_USD"] ?? "100"),
    lookbackDays: parseInt(process.env["LOOKBACK_DAYS"] ?? "30", 10),
  };
}

async function main(): Promise<void> {
  const config = loadConfig();
  const awsClient = new AWSCostClient(config.awsRegion);

  console.log("Fetching AWS cost data…");

  const [partialCostData, topServices, sevenDayAverage] = await Promise.all([
    awsClient.getYesterdayAndMTD(),
    awsClient.getTopServices(),
    awsClient.getSevenDayAverage(),
  ]);

  const costData: CostData = {
    ...partialCostData,
    forecastedSpend: 0, // populated by a future getForecast() method
  };
    
  // this is after fetching 
  const anomalyReport = analyzeSpendVariance(costData.yesterdaySpend, sevenDayAverage);

  console.log(
    `MTD: $${costData.monthToDateSpend.toFixed(2)} | Yesterday: $${costData.yesterdaySpend.toFixed(2)} | 7-day avg: $${sevenDayAverage.toFixed(2)}`
  );

  if (!exceedsThreshold(costData, config.costThreshold)) {
    console.log(
      `MTD spend $${costData.monthToDateSpend.toFixed(2)} is within threshold $${config.costThreshold}. No alert sent.`
    );
    return;
  }

  const costReport = { costData, topServices, anomalyReport };
  const payload = formatCostPayload(costReport);
  await sendWebhook(config.webhookUrl, payload);
  console.log(`Alert sent — anomaly: ${anomalyReport.isAnomaly}, variance: ${anomalyReport.percentageVariance}%`);
}

main().catch((err: unknown) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
