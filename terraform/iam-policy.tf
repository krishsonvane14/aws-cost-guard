data "aws_iam_policy_document" "cost_guard_policy" {
  statement {
    sid    = "AllowCostExplorerRead"
    effect = "Allow"

    actions = [
      "ce:GetCostAndUsage",
      "ce:GetCostForecast",
      "ce:GetUsageForecast",
      "ce:DescribeCostCategoryDefinition",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "cost_guard" {
  name        = "aws-cost-guard-policy"
  description = "Minimal read-only access for the AWS Cost Guard service"
  policy      = data.aws_iam_policy_document.cost_guard_policy.json
}

resource "aws_iam_user" "cost_guard" {
  name = "aws-cost-guard"
  path = "/services/"

  tags = {
    Project   = "aws-cost-guard"
    ManagedBy = "terraform"
  }
}

resource "aws_iam_user_policy_attachment" "cost_guard" {
  user       = aws_iam_user.cost_guard.name
  policy_arn = aws_iam_policy.cost_guard.arn
}
