#!/usr/bin/env bash
# deploy-security.sh
#
# Deploys Phase 2 — Security infrastructure for the Patent Classifier:
#   - KMS Customer Managed Key (encryption for CWL + SSM)
#   - CloudWatch Log Groups (application + Bedrock invocation logs)
#   - SSM Parameter (system prompt)
#   - Lambda Custom Resource to enable Bedrock model invocation logging
#
# Prerequisites:
#   Phase 1 (patent-classifier-iam) must already be deployed, because
#   this stack imports the AppRole and BedrockLoggingRole ARNs via
#   CloudFormation exports.
#
# Usage:
#   ./deploy-security.sh [--region <region>] [--system-prompt <text>]
#
# Defaults to us-east-1 and the standard IPC patent examiner prompt.

set -euo pipefail

# ── Defaults ───────────────────────────────────────────────────────────────────
REGION="us-east-1"
STACK_NAME="patent-classifier-security"
TEMPLATE_FILE="$(dirname "$0")/infra/phase2-security.yaml"
SYSTEM_PROMPT=""

# ── Argument parsing ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --region)
      REGION="$2"
      shift 2
      ;;
    --system-prompt)
      SYSTEM_PROMPT="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--region <region>] [--system-prompt <text>]" >&2
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

# Verify phase 1 stack is deployed before continuing
echo "Checking prerequisite: patent-classifier-iam stack..."
PHASE1_STATUS=$(aws cloudformation describe-stacks \
  --stack-name "patent-classifier-iam" \
  --region "$REGION" \
  --query "Stacks[0].StackStatus" \
  --output text 2>/dev/null || echo "NOT_FOUND")

if [[ "$PHASE1_STATUS" != "CREATE_COMPLETE" && "$PHASE1_STATUS" != "UPDATE_COMPLETE" ]]; then
  echo "ERROR: patent-classifier-iam stack is not deployed (status: $PHASE1_STATUS)." >&2
  echo "       Run deploy-phase1.sh first." >&2
  exit 1
fi
echo "  Phase 1 stack status: $PHASE1_STATUS ✓"

echo ""
echo "=================================================="
echo " Patent Classifier — Phase 2: Security"
echo "=================================================="
echo "  Stack   : $STACK_NAME"
echo "  Region  : $REGION"
echo "  Template: $TEMPLATE_FILE"
echo ""

# ── Build parameter overrides ──────────────────────────────────────────────────
PARAM_OVERRIDES=""
if [[ -n "$SYSTEM_PROMPT" ]]; then
  PARAM_OVERRIDES="ParameterKey=SystemPromptValue,ParameterValue=${SYSTEM_PROMPT}"
  echo "  Using custom system prompt."
else
  echo "  Using default system prompt (from template)."
fi

# ── Deploy ─────────────────────────────────────────────────────────────────────
echo ""
echo "Deploying CloudFormation stack..."

DEPLOY_CMD=(
  aws cloudformation deploy
  --stack-name "$STACK_NAME"
  --template-file "$TEMPLATE_FILE"
  --capabilities CAPABILITY_NAMED_IAM
  --region "$REGION"
)

if [[ -n "$PARAM_OVERRIDES" ]]; then
  DEPLOY_CMD+=(--parameter-overrides "$PARAM_OVERRIDES")
fi

"${DEPLOY_CMD[@]}"

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
echo "Verifying Bedrock invocation logging configuration..."
aws bedrock get-model-invocation-logging-configuration \
  --region "$REGION" \
  --query "loggingConfig" \
  --output json

echo ""
echo "Phase 2 complete. Security infrastructure is ready."
echo ""
echo "Next steps:"
echo "  1. Redeploy phase 1 to pick up the new IAM policy additions:"
echo "     ./deploy-phase1.sh --region $REGION"
echo "  2. Rebuild and redeploy the application container."
