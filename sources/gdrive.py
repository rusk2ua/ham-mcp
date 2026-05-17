import requests

DRIVE_API = "https://www.googleapis.com/drive/v3"


def list_files(folder_id: str) -> list[dict]:
    """List files in a publicly shared Google Drive folder."""
    params = {"q": f"'{folder_id}' in parents", "fields": "files(id,name,mimeType)"}
    return requests.get(f"{DRIVE_API}/files", params=params).json().get("files", [])


def fetch_file(file_id: str) -> bytes:
    """Download a file from Google Drive by file ID."""
    return requests.get(f"{DRIVE_API}/files/{file_id}?alt=media").content
