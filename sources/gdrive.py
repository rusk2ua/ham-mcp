import requests

DRIVE_API = "https://www.googleapis.com/drive/v3"
FOLDER_MIME = "application/vnd.google-apps.folder"


def _list_children(folder_id: str) -> list[dict]:
    params = {
        "q": f"'{folder_id}' in parents",
        "fields": "files(id,name,mimeType)",
        "pageSize": 1000,
    }
    return requests.get(f"{DRIVE_API}/files", params=params).json().get("files", [])


def list_files(folder_id: str, _path: str = "") -> list[dict]:
    """Recursively list all files in a public Google Drive folder tree.

    Returns each file as {"id", "name", "path"} where path is the
    slash-separated folder hierarchy relative to the root folder_id.
    """
    results = []
    for item in _list_children(folder_id):
        item_path = f"{_path}/{item['name']}" if _path else item["name"]
        if item["mimeType"] == FOLDER_MIME:
            results.extend(list_files(item["id"], _path=item_path))
        else:
            results.append({"id": item["id"], "name": item["name"], "path": item_path})
    return results


def fetch_file(file_id: str) -> bytes:
    """Download a file from Google Drive by file ID."""
    return requests.get(f"{DRIVE_API}/files/{file_id}?alt=media").content
