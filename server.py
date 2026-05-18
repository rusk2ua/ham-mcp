import io
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pypdf import PdfReader

from parsers import adif, cabrillo
from sources import gdrive, s3

load_dotenv()
port = int(os.getenv("PORT", "8080"))
mcp = FastMCP("ham-radio", host="0.0.0.0", port=port)

# Valid sub-folders under each year prefix
YEAR_SUBFOLDERS = {"logs", "results", "articles", "rpt", "rules"}

# Log format determined by file extension
CABRILLO_EXTENSIONS = {".cbr", ".log"}
ADIF_EXTENSIONS = {".adi"}


def _log_format(filename: str) -> str | None:
    """Return 'cabrillo', 'adif', or None based on file extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in CABRILLO_EXTENSIONS:
        return "cabrillo"
    if ext in ADIF_EXTENSIONS:
        return "adif"
    return None


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("s3://{year}/logs/{key}")
def log_file(year: str, key: str) -> str:
    """Return parsed log records as text. Format determined by file extension."""
    data = s3.fetch_file(f"{year}/logs/{key}")
    fmt = _log_format(key)
    if fmt == "adif":
        records = adif.parse(data)
        return "\n".join(str(r) for r in records)
    if fmt == "cabrillo":
        records = cabrillo.parse(data)
        return "\n".join(str(r) for r in records)
    return data.decode(errors="replace")


@mcp.resource("s3://{year}/articles/{key}")
def article_document(year: str, key: str) -> str:
    """Return extracted text from a PDF article in S3."""
    data = s3.fetch_file(f"{year}/articles/{key}")
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_files(year: str, folder: str, source: str = "s3") -> list[dict]:
    """List files in a year/folder path.

    year:   e.g. '2025'
    folder: one of logs, results, articles, rpt, rules
    source: 's3' or 'gdrive'
    """
    if folder not in YEAR_SUBFOLDERS:
        raise ValueError(f"folder must be one of {sorted(YEAR_SUBFOLDERS)}")
    prefix = f"{year}/{folder}/"
    if source == "gdrive":
        folder_id = os.getenv("GDRIVE_FOLDER_ID", "")
        return gdrive.list_files(folder_id, year=year, subfolder=folder)
    return s3.list_files(prefix)


@mcp.tool()
def search_log_by_callsign(callsign: str, year: str, log_key: str) -> list[dict]:
    """Search a log file for QSOs with a specific callsign.

    Supports ADIF (.adi) and Cabrillo (.cbr, .log) formats.
    """
    data = s3.fetch_file(f"{year}/logs/{log_key}")
    fmt = _log_format(log_key)
    if fmt == "adif":
        records = adif.parse(data)
    elif fmt == "cabrillo":
        records = cabrillo.parse(data)
    else:
        raise ValueError(f"Unrecognised log format for: {log_key}")
    call = callsign.upper()
    return [r for r in records if r.get("CALL", "").upper() == call]


@mcp.tool()
def parse_log(year: str, log_key: str) -> list[dict]:
    """Parse a log file and return QSO records. Format detected from extension."""
    data = s3.fetch_file(f"{year}/logs/{log_key}")
    fmt = _log_format(log_key)
    if fmt == "adif":
        return adif.parse(data)
    if fmt == "cabrillo":
        return cabrillo.parse(data)
    raise ValueError(f"Unrecognised log format for: {log_key}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=port)
