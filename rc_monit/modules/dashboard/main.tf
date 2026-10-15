# ---------------------------------------------------------------------------
# modules/dashboard/main.tf
#
# Deploys a CloudWatch dashboard with four sections:
#   1. Cost Attribution    (ResearchComputing/Costs custom metrics)
#   2. Spot Interruptions  (ResearchComputing/Spot custom metrics)
#   3. EC2 Utilization     (AWS/EC2 native metrics)
#   4. Storage             (AWS/S3, AWS/EFS native metrics)
# ---------------------------------------------------------------------------

locals {
  dashboard_body = templatefile("${path.module}/templates/dashboard.json.tpl", {
    projects           = var.research_projects
    s3_buckets         = var.s3_research_bucket_names
    efs_ids            = var.efs_filesystem_ids
    aws_region         = var.aws_region
    cpu_idle_threshold = var.cpu_idle_threshold
  })
}

resource "aws_cloudwatch_dashboard" "research" {
  dashboard_name = var.dashboard_name
  dashboard_body = local.dashboard_body
}
