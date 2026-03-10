/** Aggregated spend figures for a single reporting window. */
export interface CostData {
  /** Total spend for the previous calendar day, in `currency` units. */
  yesterdaySpend: number;
  /** Accumulated spend from the first of the current month to today, in `currency` units. */
  monthToDateSpend: number;
  /** AWS Cost Explorer end-of-month forecast for the current month, in `currency` units. */
  forecastedSpend: number;
  /** ISO 4217 currency code (e.g. `"USD"`). */
  currency: string;
}

/** Cost breakdown for a single AWS service. */
export interface ServiceCost {
  /** Human-readable AWS service name (e.g. `"Amazon EC2"`). */
  serviceName: string;
  /** Unblended cost for the service in the reporting period. */
  amount: number;
}

/** Anomaly detection result derived from recent spend history. */
export interface AnomalyReport {
  /** `true` when current spend deviates beyond the acceptable variance threshold. */
  isAnomaly: boolean;
  /** Rolling average of daily spend over the past 7 days, in the report's currency. */
  sevenDayAverage: number;
  /** How much today's spend differs from `sevenDayAverage`, expressed as a percentage (e.g. `42.5` = 42.5 % above average). */
  percentageVariance: number;
}

/** Top-level report produced by a single Cost Guard run. */
export interface CostReport {
  /** High-level spend figures (yesterday, MTD, forecast). */
  costData: CostData;
  /** The top 5 AWS services by spend for the reporting period. */
  topServices: [ServiceCost, ServiceCost, ServiceCost, ServiceCost, ServiceCost] | ServiceCost[];
  /** Anomaly detection summary for the current period. */
  anomalyReport: AnomalyReport;
}

/** A single field inside a Discord embed. */
export interface DiscordEmbedField {
  name: string;
  value: string;
  /** When `true`, Discord renders up to three fields side-by-side. */
  inline?: boolean;
}

/** A Discord embed object. */
export interface DiscordEmbed {
  title: string;
  description?: string;
  /** Decimal colour integer (e.g. `16711680` = red, `65280` = green). */
  color: number;
  fields: DiscordEmbedField[];
  timestamp: string;
}

/** Top-level Discord (or Slack-compatible) webhook body. */
export interface WebhookPayload {
  embeds: [DiscordEmbed];
}

export interface AppConfig {
  awsRegion: string;
  webhookUrl: string;
  costThreshold: number;
  lookbackDays: number;
}
