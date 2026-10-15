---
name: add-research-project
description: Add a new research project to the monitoring stack. Use when onboarding a new genomics or bioinformatics project that needs cost tracking, spot alarms, and dashboard visibility.
---

## Steps

1. Add the project name to `research_projects` in `terraform.tfvars`:
   ```hcl
   research_projects = [
     "genome-seq",
     "protein-fold",
     "new-project",  # ← add here
   ]
   ```

2. Run `terraform plan` and confirm the following new resources are shown:
   - One `aws_cloudwatch_metric_alarm` for cost spike (`research-cost-spike-<name>`)
   - One `aws_cloudwatch_metric_alarm` for spot burst (`research-spot-burst-<name>`)
   - Updated `aws_cloudwatch_dashboard` body (new widgets for the project)

3. Run `terraform apply` to deploy.

4. Remind the researcher to tag **all** EC2/S3/EFS/Lambda resources with:
   - `Project = <name>` — must exactly match the string added to `research_projects`
   - `Researcher = <username>`
   - `Pipeline = nextflow | snakemake | ...`

5. Optionally force an immediate cost harvest (instead of waiting up to 6 hours):
   ```bash
   aws lambda invoke --function-name research-cost-harvester /dev/null
   ```

6. Verify cost metrics appear in the dashboard under **Cost Attribution → Daily Spend by Project**.

## Notes

- The `Project` tag value on EC2 instances must exactly match the entry in `research_projects` for per-project metrics to populate.
- Cost Explorer has a 24-hour lag on newly tagged resources — the first data point may not appear until the following day.
- Spot interruption metrics only appear when actual interruptions occur. Use the test event in the README troubleshooting section to validate the pipeline.
