import axios from "axios";
import type { WebhookPayload } from "./types.js";

export async function sendWebhook(
  webhookUrl: string,
  payload: WebhookPayload
): Promise<void> {
  await axios.post(webhookUrl, payload, {
    headers: { "Content-Type": "application/json" },
    timeout: 10_000,
  });
}
