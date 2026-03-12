# ──────────────────────────────────────────────────────────────────────────────
# AWS Cost Guard — GitHub OIDC Federation
# ──────────────────────────────────────────────────────────────────────────────
# Replaces long-lived IAM access keys with short-lived OIDC tokens.
# GitHub Actions requests an OIDC token from GitHub, then exchanges it for
# temporary AWS credentials via STS AssumeRoleWithWebIdentity.
# ──────────────────────────────────────────────────────────────────────────────

# ── Variables ─────────────────────────────────────────────────────────────────

variable "github_org" {
  description = "GitHub username or organisation that owns the repository."
  type        = string
}

variable "github_repo" {
  description = "Repository name (without the org prefix)."
  type        = string
  default     = "aws-cost-guard"
}

variable "aws_region" {
  description = "AWS region for the Cost Explorer API calls."
  type        = string
  default     = "us-east-1"
}

# ── OIDC Provider ─────────────────────────────────────────────────────────────
# IMPORTANT: Only ONE GitHub OIDC provider can exist per AWS account.
# If your account already has one (e.g. from another project), import it
# instead of creating a new one:
#
#   terraform import aws_iam_openid_connect_provider.github \
#     arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com
#
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd",
  ]

  tags = {
    ManagedBy = "terraform"
    Project   = "aws-cost-guard"
  }
}

# ── IAM Role ──────────────────────────────────────────────────────────────────

resource "aws_iam_role" "cost_guard_github" {
  name = "aws-cost-guard-github-actions"

  # The StringLike condition on "sub" is the critical security gate: it scopes
  # this role to ONLY the specified repo and branch. Without it any GitHub
  # Actions workflow in ANY repository could assume the role.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/main"
          }
        }
      }
    ]
  })

  tags = {
    ManagedBy = "terraform"
    Project   = "aws-cost-guard"
  }
}

# ── Inline Policy ─────────────────────────────────────────────────────────────
# Cost Explorer does not support resource-level ARNs, so Resource = "*" is
# both correct and required here.

resource "aws_iam_role_policy" "cost_explorer_read" {
  name = "cost-explorer-read-only"
  role = aws_iam_role.cost_guard_github.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ce:GetCostAndUsage"]
        Resource = "*"
      }
    ]
  })
}

# ── Outputs ───────────────────────────────────────────────────────────────────

output "role_arn" {
  description = "Paste this into your GitHub repo secret: AWS_ROLE_ARN"
  value       = aws_iam_role.cost_guard_github.arn
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider (for reference)."
  value       = aws_iam_openid_connect_provider.github.arn
}
