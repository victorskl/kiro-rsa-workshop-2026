---
name: add-member-account-oam
description: Connect a new AWS member account to the monitoring account via CloudWatch OAM so its metrics appear in the centralised dashboard. Use when onboarding a new research team account into the multi-account setup.
---

## Steps

### In the monitoring account (this Terraform)

1. Add the new account ID to `source_account_ids` in `terraform.tfvars`:
   ```hcl
   source_account_ids = [
     "111122223333",  # existing
     "444455556666",  # ← new member account
   ]
   ```

2. Run `terraform apply` — this updates the OAM sink policy to permit the new account to create a link.

3. Retrieve the sink ARN:
   ```bash
   terraform output oam_sink_arn
   ```

### In the member account

4. Create the OAM link (run authenticated as the member account):
   ```bash
   aws oam create-link \
     --label-template '$AccountName' \
     --resource-types "AWS::CloudWatch::Metric" "AWS::Logs::LogGroup" \
     --sink-identifier "<oam_sink_arn from step 3>" \
     --region us-east-1
   ```

   Or with Terraform in the member account's workspace:
   ```hcl
   resource "aws_oam_link" "to_monitoring" {
     label_template  = "$AccountName"
     resource_types  = ["AWS::CloudWatch::Metric", "AWS::Logs::LogGroup"]
     sink_identifier = "<oam_sink_arn>"
   }
   ```

5. Confirm the link status is `Active`:
   ```bash
   aws oam list-links --region us-east-1
   ```

### Verification

6. Wait up to 5 minutes, then open the CloudWatch dashboard in the monitoring account.
   Member account metrics should appear in the EC2 Utilization panel.

## Notes

- OAM links are unidirectional — the member account pushes metrics to the monitoring account sink.
- The monitoring account dashboard uses cross-account metric queries specifying `accountId` in widget definitions.
- If the link status is `Failed`, check that the sink policy includes the member account ID and that the member account's IAM role has `oam:CreateLink` permission.
- Removing a member account: delete the `aws_oam_link` in the member account first, then remove the account ID from `source_account_ids` and re-apply.
