# ──────────────────────────────────────────────────────────────────────────────
# Usage
# ──────────────────────────────────────────────────────────────────────────────
# Attach `aws_iam_policy.cost_explorer_read_only` to the IAM user or role that
# your GitHub Actions workflow assumes (e.g. via OIDC or long-lived access keys
# stored in repository secrets).
#
# Minimal OIDC example in your workflow:
#
#   permissions:
#     id-token: write
#     contents: read
#
#   - uses: aws-actions/configure-aws-credentials@v4
#     with:
#       role-to-assume: arn:aws:iam::<ACCOUNT_ID>:role/<ROLE_NAME>
#       aws-region: us-east-1
#
# Then attach this policy to that role:
#
#   resource "aws_iam_role_policy_attachment" "cost_guard_github" {
#     role       = aws_iam_role.github_actions.name
#     policy_arn = aws_iam_policy.cost_explorer_read_only.arn
#   }
# ──────────────────────────────────────────────────────────────────────────────

data "aws_iam_policy_document" "cost_explorer_read_only" {
  statement {
    sid    = "AllowGetCostAndUsage"
    effect = "Allow"

    # Absolute minimum: only the single API call the application makes.
    actions = [
      "ce:GetCostAndUsage",
    ]

    # Cost Explorer does not support resource-level ARNs; "*" is required.
    resources = ["*"]
  }
}

resource "aws_iam_policy" "cost_explorer_read_only" {
  name        = "aws-cost-guard-cost-explorer-read-only"
  path        = "/aws-cost-guard/"
  description = "Grants the minimum permission required by AWS Cost Guard: ce:GetCostAndUsage only."
  policy      = data.aws_iam_policy_document.cost_explorer_read_only.json

  tags = {
    Project   = "aws-cost-guard"
    ManagedBy = "terraform"
  }
}
