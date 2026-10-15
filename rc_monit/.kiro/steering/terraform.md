# Terraform Conventions

- All modules must have main.tf, variables.tf, and outputs.tf.
- Every variable must have a description. Boolean variables use true/false defaults, not 1/0.
- Resource tags are never set directly on resources — always pass var.tags from the module's variables.tf.
- Use for_each over count for resources that may be added or removed (avoids index shift destroys).
- IAM policies use aws_iam_policy_document data sources, never inline JSON strings.
- Least-privilege IAM: scope cloudwatch:PutMetricData with a cloudwatch:namespace condition, not resource *.
- lifecycle { ignore_changes } is required on any Secrets Manager secret_string that holds a real credential.
- archive_file data sources output to the same directory as the source file, not /tmp.
- All aws_cloudwatch_log_group resources set retention_in_days (never unlimited).
- Module outputs expose ARNs and names, not full resource objects.
- provider aliases (aws.management) are used only for resources that must run in the management account (Cost Explorer tag activation).
