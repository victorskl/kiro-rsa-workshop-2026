# Tagging Strategy

Required tags on every AWS resource: Project, Researcher, Team, Environment, Pipeline, CostCenter.

- Tags are applied globally via default_tags on the AWS provider — never set individually per resource.
- The modules/tagging module must be called first in main.tf; its output feeds provider default_tags.
- Tag values must never be empty strings. The tagging module uses a terraform_data precondition to enforce this at plan time.
- research_projects in terraform.tfvars is the single source of truth for active project identifiers. Adding a project here is sufficient — it automatically creates cost alarms, spot alarms, and dashboard widgets.
- The Project tag value on EC2 instances must exactly match an entry in research_projects for cost metrics to appear in per-project dashboard widgets.
