#!/usr/bin/env bash
# Deploy ham-mcp to AWS Lambda + API Gateway using AWS SAM.
# First run: sam deploy --guided (interactive, saves config to samconfig.toml)
# Subsequent runs: sam deploy
set -euo pipefail
cd "$(dirname "$0")"

command -v sam >/dev/null 2>&1 || pip install aws-sam-cli

sam build

if [ ! -f samconfig.toml ]; then
  echo "First deployment — running guided setup..."
  sam deploy --guided
else
  sam deploy
fi

echo ""
echo "Deployment complete. Use the McpEndpoint URL from the output above"
echo "in your MCP client config with transport: sse"
