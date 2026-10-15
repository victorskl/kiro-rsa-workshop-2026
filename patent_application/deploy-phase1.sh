#!/usr/bin/env bash
# deploy-phase1.sh
#
# Deploys Phase 1 of the Patent Classifier infrastructure:
# the IAM roles required by the application and App Runner.
#
# Deployment order:
#   1. deploy-phase1.sh   — creates AppRole + EcrAccessRole + BedrockLoggingRole
#   2. deploy-security.sh — creates KMS key, CWL log groups, SSM parameter,
#                           Bedrock invocation logging (imports phase1 role ARNs)
#   3. deploy-phase1.sh   — re-run to attach the new SSM/KMS/CWL policies that
#                           reference phase2 KMS key and log group ARN exports
#
# Note: On first deploy, run phase1 once before phase2 so the role ARNs exist
# for the phase2 KMS key policy grants. Then re-run phase1 to attach the
# additional policies that import phase2 outputs (KMS key ARN, log group ARNs).
#
# Usage:
#   ./deploy-phase1.sh [--region <region>]
#
# Defaults to us-east-1 if --region is not supplied.

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
REGION="us-east-1"
STACK_NAME="patent-classifier-iam"
TEMPLATE_FILE="$(dirname "$0")/infra/phase1-iam.yaml"

# ── Argument parsing ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --region)
      REGION="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--region <region>]" >&2
      exit 1
      ;;
  esac
done

# ── Pre-flight checks ──────────────────────────────────────────────────────────
if ! command -v aws &>/dev/null; then
  echo "ERROR: AWS CLI is not installed or not on PATH." >&2
  exit 1
fi

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "ERROR: Template not found at $TEMPLATE_FILE" >&2
  exit 1
fi

echo "=================================================="
echo " Patent Classifier — Phase 1: IAM Foundations"
echo "=================================================="
echo "  Stack  : $STACK_NAME"
echo "  Region : $REGION"
echo "  Template: $TEMPLATE_FILE"
echo ""

# ── Deploy ─────────────────────────────────────────────────────────────────────
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE_FILE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION"

# ── Verify and display outputs ─────────────────────────────────────────────────
echo ""
echo "Stack status:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].StackStatus" \
  --output text

echo ""
echo "Stack outputs:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[*].{Key:OutputKey,Value:OutputValue}" \
  --output table

echo ""
echo "Phase 1 complete. IAM roles are ready for Phase 2."
