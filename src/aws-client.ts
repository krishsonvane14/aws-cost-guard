import {
  CostExplorerClient,
  GetCostAndUsageCommand,
  type GetCostAndUsageCommandInput,
} from "@aws-sdk/client-cost-explorer";
import type { ServiceCost } from "./types.js";

/** Raw aggregated result returned by a single Cost Explorer query. */
export interface CostEntry {
  timePeriod: { start: string; end: string };
  totalAmount: number;
  currency: string;
  services: ServiceCost[];
}

export function createCostExplorerClient(region: string): CostExplorerClient {
  return new CostExplorerClient({ region });
}

export async function fetchMonthlyCosts(
  client: CostExplorerClient,
  startDate: string,
  endDate: string
): Promise<CostEntry> {
  const input: GetCostAndUsageCommandInput = {
    TimePeriod: { Start: startDate, End: endDate },
    Granularity: "MONTHLY",
    Metrics: ["UnblendedCost"],
    GroupBy: [{ Type: "DIMENSION", Key: "SERVICE" }],
  };

  const response = await client.send(new GetCostAndUsageCommand(input));

  const result = response.ResultsByTime?.[0];
  if (!result) {
    throw new Error("No cost data returned from AWS Cost Explorer");
  }

  const services: ServiceCost[] = (result.Groups ?? []).map((group) => ({
    serviceName: group.Keys?.[0] ?? "Unknown",
    amount: parseFloat(group.Metrics?.["UnblendedCost"]?.Amount ?? "0"),
  }));

  const total = result.Total?.["UnblendedCost"];

  return {
    timePeriod: {
      start: result.TimePeriod?.Start ?? startDate,
      end: result.TimePeriod?.End ?? endDate,
    },
    totalAmount: parseFloat(total?.Amount ?? "0"),
    currency: total?.Unit ?? "USD",
    services,
  };
}
