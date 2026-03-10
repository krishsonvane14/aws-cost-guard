---
description: "Use when writing, editing, or reviewing any code in the aws-cost-guard project. Covers ESM conventions, AWS SDK v3 patterns, TypeScript strictness rules, and project structure."
applyTo: "src/**/*.ts"
---

# AWS Cost Guard — Project Conventions

## Module System
- Always use ESM `import`/`export`. Never use `require()` or `module.exports`.
- All intra-project imports **must** use the `.js` extension (required by `NodeNext` resolution):
  ```ts
  // correct
  import { fetchMonthlyCosts } from "./aws-client.js";
  // wrong
  import { fetchMonthlyCosts } from "./aws-client";
  ```

## TypeScript
- `strict: true` plus `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` are enabled — do not suppress or work around them.
- Prefer `type` imports for type-only symbols: `import type { Foo } from "./types.js"`.
- Avoid `any`; use `unknown` at system boundaries (env vars, API responses) and narrow explicitly.
- All exported functions must have explicit return types.

## AWS SDK v3
- Always instantiate `CostExplorerClient` via `createCostExplorerClient()` in `aws-client.ts`; never create raw clients elsewhere.
- Use `import type` for SDK input/output shapes; only import the concrete `Command` classes as values.
- Destructure responses defensively — SDK fields are all optional; always provide fallbacks.

## Environment & Config
- All env vars are read **once** in `loadConfig()` inside `src/index.ts`.
- Required vars must be validated at startup with an explicit error message; never silently fall back to `undefined`.
- Store secrets in `.env` (gitignored). Provide a `.env.example` for every var the app reads.

## HTTP (Axios)
- All `axios.post` calls must include a `timeout` in milliseconds.
- Wrap outbound calls in `notifier.ts` only — no direct Axios usage elsewhere.

## Error Handling
- Top-level `main()` must catch and `process.exit(1)` on fatal errors.
- Prefer typed errors; annotate `catch (err: unknown)` and narrow before accessing properties.

## Project Structure
```
src/
  index.ts       — entry point, config loading, orchestration
  aws-client.ts  — CostExplorer client factory + data fetching
  formatter.ts   — pure data transformation (no I/O)
  notifier.ts    — webhook delivery via Axios
  types.ts       — shared TypeScript interfaces only (no logic)
terraform/
  iam-policy.tf  — least-privilege IAM policy for the service account
```

## Terraform
- Use `aws_iam_policy_document` data source for all policy documents (no inline JSON strings).
- IAM resources follow the principle of least privilege — only `ce:Get*` and `ce:Describe*` actions.
- All resources must have a `ManagedBy = "terraform"` tag.
