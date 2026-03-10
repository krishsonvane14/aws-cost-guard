---
description: "Use when writing, editing, or reviewing any code in the aws-cost-guard project. Covers Python conventions, boto3 patterns, dataclass usage, and project structure."
applyTo: "src/**/*.py"
---

# AWS Cost Guard — Project Conventions

## Language & Runtime
- Python 3.11+, type hints on all public functions.
- Use `from __future__ import annotations` at the top of every module.
- Data structures are `@dataclass(frozen=True)` in `models.py` — never plain dicts.

## AWS (boto3)
- All Cost Explorer interaction is in `aws_client.py` via the `AWSCostClient` class.
- Never instantiate a boto3 client outside of `AWSCostClient.__init__`.
- Parse SDK string amounts to `float` using the private `_parse_amount` helper; never call `float()` directly on untrusted SDK data.
- Wrap every SDK call in a `try/except` that re-raises as `RuntimeError` with a descriptive message.

## HTTP (requests)
- All outbound HTTP lives in `notifier.py`. No other module should import `requests`.
- Every `requests.post` must include a `timeout` in seconds.
- Non-2xx responses must raise `RuntimeError` with the status code and response body.

## Environment & Config
- All env vars are read **once** in `_load_config()` inside `main.py`.
- Required vars must be validated at startup with an explicit error message; never silently fall back to `None`.
- Store secrets in `.env` (gitignored). `.env.example` must list every variable the app reads.

## Error Handling
- `main()` is the only entry point; it catches all exceptions and calls `sys.exit(1)` on failure.
- Use typed exceptions (`RuntimeError`, `SystemExit`) — never bare `except:`.

## Project Structure
```
src/
  __init__.py        — package marker
  main.py            — entry point, config loading, orchestration
  aws_client.py      — AWSCostClient class (boto3 wrapper)
  anomaly_engine.py  — analyze_spend_variance (pure logic)
  formatter.py       — Discord embed formatting (no I/O)
  notifier.py        — webhook delivery via requests
  models.py          — frozen dataclasses (CostData, ServiceCost, AnomalyReport, CostReport)
  mock_test.py       — end-to-end mock using static fixtures
terraform/
  iam-policy.tf      — least-privilege IAM policy for the service account
```

## Terraform
- Use `aws_iam_policy_document` data source for all policy documents (no inline JSON strings).
- IAM resources follow the principle of least privilege — only `ce:GetCostAndUsage`.
- All resources must have a `ManagedBy = "terraform"` tag.
