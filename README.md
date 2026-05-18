# ham-mcp

An [MCP](https://modelcontextprotocol.io) server that connects ham radio logs, contest results, and documents to AI assistants like [Kiro CLI](https://kiro.dev) and [Claude Desktop](https://claude.ai/download).

Point your AI at an S3 bucket or Google Drive folder full of ADIF logs, Cabrillo contest files, and PDFs — then ask it questions in plain English.

---

## What It Does

### Log & document access

| Capability | Example prompt |
|------------|---------------|
| List log files | *"List all the log files in the data lake."* |
| Search by callsign | *"Find all QSOs with W1AW across every ARRL DX log."* |
| Parse contest logs | *"How many QSOs were on 40m in the 2024 CQ WW Cabrillo log?"* |
| Summarize PDFs | *"Summarize the Field Day 2023 results document."* |
| List documents | *"What PDFs are in the data lake?"* |

### Multi-year trend analysis

| Capability | Example prompt |
|------------|---------------|
| Year-over-year QSO count | *"Compare total QSO counts for ARRL DX from 2020 through 2024. Show a year-by-year table."* |
| Band trend | *"How has our 10m QSO count changed each year in CQ WW? Is there a solar cycle pattern?"* |
| Score progression | *"Pull the claimed scores from each Field Day results PDF and chart the trend."* |
| Mode breakdown | *"What percentage of our QSOs were CW vs SSB vs digital in each contest year?"* |
| Multiplier trend | *"How have our DXCC multipliers changed year over year in ARRL DX?"* |
| Best vs worst year | *"Which year was our strongest ARRL DX performance and what made it different?"* |

### Cross-contest comparisons

| Capability | Example prompt |
|------------|---------------|
| Contest comparison | *"Compare our QSO rates in ARRL DX vs CQ WW over the last three years."* |
| Operator activity | *"Which operators appear most frequently across all contest logs?"* |
| Band-by-band breakdown | *"Across all contests in 2024, which band produced the most QSOs?"* |

### Callsign & contact research

| Capability | Example prompt |
|------------|---------------|
| Contact history | *"How many times have we worked W1AW total, and in which contests?"* |
| New entities | *"List any DXCC entities we only worked once across all logs."* |
| Dupe analysis | *"Find callsigns that appear in both the 2023 and 2024 ARRL DX logs."* |

> **Note on visualization:** The AI can reason over this data and produce narrative summaries or tables, but actual chart rendering (line graphs, bar charts) would require either a code interpreter environment (like Claude's analysis tool) or a separate visualization step. The prompts above are worded to ask for tables and comparisons, which any MCP-connected AI can handle directly.

---

## Requirements

- Python 3.11+
- AWS credentials configured (`aws configure`) — needed for S3 access
- An S3 bucket **or** a publicly shared Google Drive folder with your data

---

## Quick Start

```bash
git clone https://github.com/rusk2ua/ham-mcp.git
cd ham-mcp
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your S3 bucket name and/or Google Drive folder ID
./run_local.sh
```

Then add the server to your AI client (see [Client Configuration](#client-configuration)).

---

## S3 Bucket Layout

Files are organized by year, then by folder. Log format is detected automatically from the file extension.

```
s3://your-bucket/
└── 2025/
    ├── logs/       # *.adi = ADIF,  *.cbr / *.log = Cabrillo
    ├── results/    # contest result files
    ├── articles/   # *.pdf articles and references
    ├── rpt/        # reports
    └── rules/      # contest rules documents
```

---

## Project Structure

```
ham-mcp/
├── server.py            # MCP server (resources + tools)
├── sources/
│   ├── s3.py            # S3 connector
│   └── gdrive.py        # Google Drive connector (public folders)
├── parsers/
│   ├── adif.py          # ADIF log parser
│   └── cabrillo.py      # Cabrillo log parser
├── requirements.txt
├── run_local.sh         # Run server locally
├── run_aws.sh           # Deploy to AWS Lambda
├── template.yaml        # AWS SAM template
└── .env.example
```

---

## Client Configuration

### Kiro CLI

Add to `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "ham-radio": {
      "command": "python",
      "args": ["/path/to/ham-mcp/server.py"]
    }
  }
}
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ham-radio": {
      "command": "python",
      "args": ["/path/to/ham-mcp/server.py"]
    }
  }
}
```

### Cline (VS Code extension)

Open the Cline extension settings in VS Code, navigate to **MCP Servers**, and add:

```json
{
  "ham-radio": {
    "command": "python",
    "args": ["/path/to/ham-mcp/server.py"],
    "disabled": false,
    "autoApprove": []
  }
}
```

Alternatively, edit `~/.vscode/cline_mcp_settings.json` directly with the same block.

---

## AWS Serverless Deployment

For shared access without everyone running a local server, deploy to ECS Fargate + ALB. A single script handles everything: ECR repo creation, Docker build/push, and CloudFormation deploy.

**Requirements:** AWS CLI, Docker, credentials with ECS/ECR/CloudFormation/IAM permissions.

```bash
./deploy.sh --bucket your-s3-bucket-name
```

Optional flags:
```
--region   AWS region (default: us-east-1)
--stack    CloudFormation stack name (default: ham-mcp)
--gdrive   Google Drive folder ID (optional)
```

The script prints the MCP endpoint URL when complete. Use it in your client config:

```json
{
  "mcpServers": {
    "ham-radio": {
      "url": "http://<alb-dns-name>/sse",
      "transport": "sse"
    }
  }
}
```

The base URL stays the same across redeployments as long as you use the same stack name. To update after code changes, just re-run `./deploy.sh` with the same arguments.

**Cost:** ~$9/month for 1 Fargate task (0.25 vCPU / 0.5 GB). The ALB adds ~$16/month. Total ~$25/month for a always-on shared server.

---

## Google Drive

The Google Drive connector works with folders shared as **"Anyone with the link can view."** Set `GDRIVE_FOLDER_ID` in `.env` to the ID from the share URL:

```
https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        this is your GDRIVE_FOLDER_ID
```

Pass `source="gdrive"` to the `list_files` tool.

---

## Cabrillo Parser Note

Cabrillo QSO field positions vary by contest (ARRL DX, CQ WW, Field Day, etc.). The parser in `parsers/cabrillo.py` handles the common 10-column format. If your contest uses a different layout, adjust the field indices in that file.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NoCredentialsError` | Run `aws configure` or set `AWS_PROFILE` in `.env` |
| Google Drive returns empty list | Confirm folder is shared as "Anyone with the link" |
| PDF text is empty | PDF is image-only — run OCR before uploading |
| MCP client can't connect | Use the absolute path to `server.py` in client config |
| Lambda timeout | Increase `Timeout` in `template.yaml` (max 29s for API GW) |
| "no authorization support detected" | Ensure you're using `transport: "sse"` and the `/sse` path suffix |

---

## License

MIT
