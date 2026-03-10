export interface CostEntry {
  timePeriod: {
    start: string;
    end: string;
  };
  totalAmount: string;
  unit: string;
  services: ServiceCost[];
}

export interface ServiceCost {
  serviceName: string;
  amount: string;
  unit: string;
}

export interface WebhookPayload {
  title: string;
  period: string;
  totalCost: string;
  currency: string;
  services: ServiceCost[];
  timestamp: string;
}

export interface AppConfig {
  awsRegion: string;
  webhookUrl: string;
  costThreshold: number;
  lookbackDays: number;
}
