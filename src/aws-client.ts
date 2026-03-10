import {
  CostExplorerClient,
  GetCostAndUsageCommand,
  type GetCostAndUsageCommandInput,
} from "@aws-sdk/client-cost-explorer";
import type { CostData, ServiceCost } from "./types.js";

/** Returns an ISO date string (YYYY-MM-DD) offset by `offsetDays` from today. */
function isoDate(offsetDays: number = 0): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + offsetDays);
  return d.toISOString().split("T")[0] as string;
}

/** Safely parses an AWS Cost Explorer amount string to a `number`. */
function parseAmount(raw: string | undefined): number {
  const n = parseFloat(raw ?? "0");
  return isFinite(n) ? n : 0;
}

export class AWSCostClient {
  private readonly client: CostExplorerClient;

  constructor(region: string) {
    this.client = new CostExplorerClient({ region });
  }

  /**
   * Fetches UnblendedCost for yesterday (single day) and the current
   * month-to-date period in two separate queries, then returns a
   * partial {@link CostData} (without `forecastedSpend`).
   */
  async getYesterdayAndMTD(): Promise<Pick<CostData, "yesterdaySpend" | "monthToDateSpend" | "currency">> {
    const today = isoDate();
    const yesterday = isoDate(-1);
    const monthStart = today.slice(0, 8) + "01"; // YYYY-MM-01

    const makeInput = (start: string, end: string): GetCostAndUsageCommandInput => ({
      TimePeriod: { Start: start, End: end },
      Granularity: "DAILY",
      Metrics: ["UnblendedCost"],
    });

    try {
      const [ydResponse, mtdResponse] = await Promise.all([
        this.client.send(new GetCostAndUsageCommand(makeInput(yesterday, today))),
        this.client.send(new GetCostAndUsageCommand(makeInput(monthStart, today))),
      ]);

      const ydTotal = ydResponse.ResultsByTime?.[0]?.Total?.["UnblendedCost"];
      const currency = ydTotal?.Unit ?? "USD";

      const monthToDateSpend = (mtdResponse.ResultsByTime ?? []).reduce(
        (sum, r) => sum + parseAmount(r.Total?.["UnblendedCost"]?.Amount),
        0
      );

      return {
        yesterdaySpend: parseAmount(ydTotal?.Amount),
        monthToDateSpend,
        currency,
      };
    } catch (err) {
      throw new Error(
        `Failed to fetch yesterday/MTD costs: ${err instanceof Error ? err.message : String(err)}`
      );
    }
  }

  /**
   * Fetches the top 5 most expensive AWS services for the current billing
   * period (1st of the month to today), grouped by the SERVICE dimension.
   */
  async getTopServices(): Promise<ServiceCost[]> {
    const today = isoDate();
    const monthStart = today.slice(0, 8) + "01";

    const input: GetCostAndUsageCommandInput = {
      TimePeriod: { Start: monthStart, End: today },
      Granularity: "MONTHLY",
      Metrics: ["UnblendedCost"],
      GroupBy: [{ Type: "DIMENSION", Key: "SERVICE" }],
    };

    try {
      const response = await this.client.send(new GetCostAndUsageCommand(input));
      const groups = response.ResultsByTime?.[0]?.Groups ?? [];

      return groups
        .map((g): ServiceCost => ({
          serviceName: g.Keys?.[0] ?? "Unknown",
          amount: parseAmount(g.Metrics?.["UnblendedCost"]?.Amount),
        }))
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 5);
    } catch (err) {
      throw new Error(
        `Failed to fetch top services: ${err instanceof Error ? err.message : String(err)}`
      );
    }
  }

  /**
   * Fetches daily UnblendedCost for the last 7 complete days and returns
   * their arithmetic mean.
   */
  async getSevenDayAverage(): Promise<number> {
    const end = isoDate();   // today (exclusive upper bound in Cost Explorer)
    const start = isoDate(-7);

    const input: GetCostAndUsageCommandInput = {
      TimePeriod: { Start: start, End: end },
      Granularity: "DAILY",
      Metrics: ["UnblendedCost"],
    };

    try {
      const response = await this.client.send(new GetCostAndUsageCommand(input));
      const days = response.ResultsByTime ?? [];

      if (days.length === 0) return 0;

      const total = days.reduce(
        (sum, r) => sum + parseAmount(r.Total?.["UnblendedCost"]?.Amount),
        0
      );

      return total / days.length;
    } catch (err) {
      throw new Error(
        `Failed to fetch 7-day average: ${err instanceof Error ? err.message : String(err)}`
      );
    }
  }
}
