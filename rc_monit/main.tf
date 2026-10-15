# ---------------------------------------------------------------------------
# main.tf — root module
#
# Wires together all sub-modules.  Providers are declared in providers.tf;
# the tagging module must be instantiated before the providers so its output
# can be referenced in the provider default_tags block.
# ---------------------------------------------------------------------------

# ── Tagging (shared infrastructure tags) ──────────────────────────────────

module "tags" {
  source = "./modules/tagging"

  project     = var.default_project
  researcher  = var.default_researcher
  team        = var.default_team
  environment = var.environment
  pipeline    = var.default_pipeline
  cost_center = var.cost_center
}

# ── Cost Allocation Tags (management account) ─────────────────────────────

module "cost_allocation_tags" {
  source = "./modules/cost_allocation_tags"

  providers = {
    aws = aws.management
  }
}

# ── Cost Harvester Lambda ──────────────────────────────────────────────────

module "cost_harvester" {
  source = "./modules/cost_harvester"

  aws_region        = var.aws_region
  research_projects = var.research_projects
  tags              = module.tags.tags
}

# ── Spot Interruption Tracker ─────────────────────────────────────────────

module "spot_tracker" {
  source = "./modules/spot_tracker"

  tags = module.tags.tags
}

# ── CloudWatch Alarms ─────────────────────────────────────────────────────

module "alarms" {
  source = "./modules/alarms"

  research_projects                 = var.research_projects
  cost_alarm_threshold_usd          = var.cost_alarm_threshold_usd
  cpu_idle_threshold_percent        = var.cpu_idle_threshold_percent
  spot_interruption_alarm_threshold = var.spot_interruption_alarm_threshold
  sns_topic_arn                     = module.notifications.sns_topic_arn
  tags                              = module.tags.tags
}

# ── Notifications (SNS + Slack Lambda) ───────────────────────────────────

module "notifications" {
  source = "./modules/notifications"

  slack_webhook_secret_name = var.slack_webhook_secret_name
  alarm_email_addresses     = var.alarm_email_addresses
  dashboard_name            = var.dashboard_name
  aws_region                = var.aws_region
  tags                      = module.tags.tags
}

# ── CloudWatch Dashboard ──────────────────────────────────────────────────

module "dashboard" {
  source = "./modules/dashboard"

  dashboard_name           = var.dashboard_name
  aws_region               = var.aws_region
  research_projects        = var.research_projects
  efs_filesystem_ids       = var.efs_filesystem_ids
  s3_research_bucket_names = var.s3_research_bucket_names
  source_account_ids       = var.source_account_ids
  cpu_idle_threshold       = var.cpu_idle_threshold_percent
  tags                     = module.tags.tags
}

# ── CloudWatch OAM (multi-account metric sharing) ─────────────────────────

module "oam" {
  source = "./modules/oam"

  source_account_ids = var.source_account_ids
  tags               = module.tags.tags
}
