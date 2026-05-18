#!/usr/bin/env bash
# deploy.sh — Build, push, and deploy ham-mcp to ECS Fargate.
#
# Usage:
#   ./deploy.sh --bucket <s3-bucket> [--region us-east-1] [--stack ham-mcp] [--gdrive <folder-id>]
#
# Requirements: aws cli, docker
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
REGION="us-east-1"
STACK="ham-mcp"
GDRIVE_FOLDER_ID=""

# ── Args ──────────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --bucket)  S3_BUCKET="$2";       shift 2 ;;
    --region)  REGION="$2";          shift 2 ;;
    --stack)   STACK="$2";           shift 2 ;;
    --gdrive)  GDRIVE_FOLDER_ID="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "${S3_BUCKET:-}" ]]; then
  echo "Error: --bucket is required"
  exit 1
fi

ACCOUNT=$(aws sts get-caller-identity --query Account --output text --region "$REGION")
ECR_REPO="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/ham-mcp"

# ── ECR repo (idempotent) ──────────────────────────────────────────────────────
aws ecr describe-repositories --repository-names ham-mcp --region "$REGION" >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name ham-mcp --region "$REGION" >/dev/null

# ── Build & push ───────────────────────────────────────────────────────────────
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

IMAGE_URI="$ECR_REPO:$(git rev-parse --short HEAD)"
docker build -t "$IMAGE_URI" "$(dirname "$0")"
docker push "$IMAGE_URI"

# ── Discover default VPC & subnets ────────────────────────────────────────────
VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" \
  --filters "Name=isDefault,Values=true" \
  --query "Vpcs[0].VpcId" --output text)

SUBNET_IDS=$(aws ec2 describe-subnets --region "$REGION" \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=default-for-az,Values=true" \
  --query "Subnets[*].SubnetId" --output text | tr '\t' ',')

# ── Deploy CloudFormation ──────────────────────────────────────────────────────
aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK" \
  --template-file "$(dirname "$0")/ecs-template.yaml" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
      S3BucketName="$S3_BUCKET" \
      ImageUri="$IMAGE_URI" \
      VpcId="$VPC_ID" \
      SubnetIds="$SUBNET_IDS" \
      GdriveFolderId="$GDRIVE_FOLDER_ID"

# ── Print endpoint ─────────────────────────────────────────────────────────────
echo ""
echo "✅ Deployed. MCP endpoint:"
aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='McpEndpoint'].OutputValue" --output text
