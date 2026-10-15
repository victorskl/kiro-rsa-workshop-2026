# ---------------------------------------------------------------------------
# modules/tagging/variables.tf
# ---------------------------------------------------------------------------

variable "project" {
  description = "Research project identifier (e.g. genome-seq-2026)."
  type        = string
}

variable "researcher" {
  description = "Researcher / owner username (e.g. jsmith)."
  type        = string
}

variable "team" {
  description = "Team or department name (e.g. computational-bio)."
  type        = string
}

variable "environment" {
  description = "Deployment environment: prod | staging | dev."
  type        = string

  validation {
    condition     = contains(["prod", "staging", "dev"], var.environment)
    error_message = "environment must be one of: prod, staging, dev."
  }
}

variable "pipeline" {
  description = "Pipeline toolchain (e.g. nextflow | snakemake | platform)."
  type        = string
}

variable "cost_center" {
  description = "Finance cost-center code (e.g. CC-4821)."
  type        = string
}

variable "additional_tags" {
  description = "Optional map of extra tags merged into the output. Required tags take precedence."
  type        = map(string)
  default     = {}
}
