# ham-mcp

An [MCP](https://modelcontextprotocol.io) server that connects ham radio logs, contest results, and documents to AI assistants like [Kiro CLI](https://kiro.dev) and [Claude Desktop](https://claude.ai/download).

Point your AI at an S3 bucket or Google Drive folder full of ADIF logs, Cabrillo contest files, and PDFs — then ask it questions in plain English.

---

## What It Does

| Capability | Example prompt |
|------------|---------------|
| List log files | *"List all the log files in the data lake."* |
| Search by callsign | *"Find all QSOs with W1AW in the ARRL-DX-2024 log."* |
| Parse contest logs | *"How many QSOs were on 40m in the Cabrillo log?"* |
| Summarize PDFs | *"Summarize the Field Day results document."* |
| List documents | *"What PDFs are in the data lake?"* |

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

```
s3://your-bucket/
├── logs/adif/          # *.adi, *.adif files
├── logs/cabrillo/      # *.cbr, *.log files
└── documents/          # *.pdf contest results, band plans, etc.
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

For shared access without everyone running a local server, deploy to AWS Lambda + API Gateway. At 1–2 concurrent users this costs effectively nothing (within Lambda free tier).

```bash
./run_aws.sh
```

The script runs `sam build` and `sam deploy`. On first run it prompts for stack name, region, and S3 bucket for deployment artifacts. Subsequent runs redeploy automatically.

After deployment, use the `McpEndpoint` URL from the CloudFormation outputs in your client config:

```json
{
  "mcpServers": {
    "ham-radio": {
      "url": "https://<api-id>.execute-api.us-east-1.amazonaws.com",
      "transport": "sse"
    }
  }
}
```

---

## Google Drive

The Google Drive connector works with folders shared as **"Anyone with the link can view."** Set `GDRIVE_FOLDER_ID` in `.env` to the ID from the share URL:

```
https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        this is your GDRIVE_FOLDER_ID
```

Pass `source="gdrive"` to the `list_logs` or `list_documents` tools.

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

---

## License

MIT
