# ---------------------------------------------------------------------------
# modules/oam/main.tf
#
# Sets up CloudWatch Observability Access Manager (OAM) for cross-account
# metric sharing.
#
# Architecture:
#   - This module runs in the MONITORING account and creates:
#       * An OAM sink — the central ingestion point for shared telemetry
#       * A sink policy — allows specified source accounts to link to it
#   - Each source (member) account must create an OAM link that points
#     to this sink's ARN.  The aws_oam_link resources below are created
#     using provider aliases (one per source account); in practice teams
#     often manage source-account links via a separate Terraform workspace
#     or a for_each over assumed-role providers.
#
# For simplicity this module creates the sink + policy in the monitoring
# account and outputs the sink ARN so source accounts can reference it.
# Source-account links are managed separately (see README.md).
# ---------------------------------------------------------------------------

data "aws_caller_identity" "monitoring" {}

# ── OAM Sink (monitoring account) ─────────────────────────────────────────

resource "aws_oam_sink" "monitoring" {
  name = "research-computing-monitoring"
  tags = var.tags
}

# Sink policy: allow each source account to create a link sharing
# metrics and CloudWatch Logs.
resource "aws_oam_sink_policy" "monitoring" {
  sink_identifier = aws_oam_sink.monitoring.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { AWS = [for id in var.source_account_ids : "arn:aws:iam::${id}:root"] }
        Action    = ["oam:CreateLink", "oam:UpdateLink"]
        Resource  = "*"
        Condition = {
          StringEquals = {
            "oam:ResourceTypes" = [
              "AWS::CloudWatch::Metric",
              "AWS::Logs::LogGroup",
            ]
          }
        }
      }
    ]
  })
}
