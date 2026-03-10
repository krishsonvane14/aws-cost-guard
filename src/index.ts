import "dotenv/config";
import { createCostExplorerClient, fetchMonthlyCosts } from "./aws-client.js";
import { exceedsThreshold, formatCostPayload } from "./formatter.js";
import { sendWebhook } from "./notifier.js";
import type { AppConfig } from "./types.js";

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

function getDateRange(lookbackDays: number): { start: string; end: string } {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - lookbackDays);

  return {
    start: start.toISOString().split("T")[0] as string,
    end: end.toISOString().split("T")[0] as string,
  };
}

async function main(): Promise<void> {
  const config = loadConfig();
  const client = createCostExplorerClient(config.awsRegion);
  const { start, end } = getDateRange(config.lookbackDays);

  console.log(`Fetching AWS costs from ${start} to ${end}…`);
  const costEntry = await fetchMonthlyCosts(client, start, end);

  if (!exceedsThreshold(costEntry, config.costThreshold)) {
    console.log(
      `Cost $${costEntry.totalAmount} is within threshold $${config.costThreshold}. No alert sent.`
    );
    return;
  }

  const payload = formatCostPayload(costEntry);
  await sendWebhook(config.webhookUrl, payload);
  console.log(`Alert sent: ${payload.title}`);
}

main().catch((err: unknown) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
