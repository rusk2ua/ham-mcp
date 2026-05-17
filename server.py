import io
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pypdf import PdfReader

from parsers import adif, cabrillo
from sources import gdrive, s3

load_dotenv()
mcp = FastMCP("ham-radio")


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("s3://logs/adif/{key}")
def adif_log(key: str) -> str:
    """Return parsed ADIF log records as text."""
    data = s3.fetch_file(f"logs/adif/{key}")
    records = adif.parse(data)
    return "\n".join(str(r) for r in records)


@mcp.resource("s3://documents/{key}")
def pdf_document(key: str) -> str:
    """Return extracted text from a PDF in S3."""
    data = s3.fetch_file(f"documents/{key}")
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_logs(source: str = "s3") -> list[dict]:
    """List available log files. source: 's3' or 'gdrive'"""
    if source == "gdrive":
        return gdrive.list_files(os.getenv("GDRIVE_FOLDER_ID", ""))
    return s3.list_files("logs/")


@mcp.tool()
def search_log_by_callsign(callsign: str, log_key: str) -> list[dict]:
    """Search an ADIF log file for QSOs with a specific callsign."""
    data = s3.fetch_file(f"logs/adif/{log_key}")
    records = adif.parse(data)
    call = callsign.upper()
    return [r for r in records if r.get("CALL", "").upper() == call]


@mcp.tool()
def parse_cabrillo(log_key: str) -> list[dict]:
    """Parse a Cabrillo contest log and return QSO records."""
    data = s3.fetch_file(f"logs/cabrillo/{log_key}")
    return cabrillo.parse(data)


@mcp.tool()
def list_documents(source: str = "s3") -> list[dict]:
    """List PDF documents in the data lake."""
    if source == "gdrive":
        return gdrive.list_files(os.getenv("GDRIVE_FOLDER_ID", ""))
    return s3.list_files("documents/")


# ── Lambda entry point (for AWS deployment) ───────────────────────────────────

try:
    from mcp.server.lambda_handler import create_handler
    handler = create_handler(mcp)
except ImportError:
    pass  # Not running on Lambda

if __name__ == "__main__":
    mcp.run()
