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


def _find_child_folder(parent_id: str, name: str) -> str | None:
    """Return the ID of a named child folder, or None if not found."""
    for item in _list_children(parent_id):
        if item["mimeType"] == FOLDER_MIME and item["name"] == name:
            return item["id"]
    return None


def list_files(root_folder_id: str, year: str = "", subfolder: str = "", _path: str = "") -> list[dict]:
    """List files under root_folder_id/year/subfolder (if provided), else recursively.

    Returns each file as {"id", "name", "path"}.
    """
    folder_id = root_folder_id

    if year:
        folder_id = _find_child_folder(folder_id, year)
        if folder_id is None:
            return []
        if subfolder:
            folder_id = _find_child_folder(folder_id, subfolder)
            if folder_id is None:
                return []
            _path = f"{year}/{subfolder}"

    return _list_flat(folder_id, _path)


def _list_flat(folder_id: str, _path: str = "") -> list[dict]:
    """Recursively list all files under folder_id."""
    results = []
    for item in _list_children(folder_id):
        item_path = f"{_path}/{item['name']}" if _path else item["name"]
        if item["mimeType"] == FOLDER_MIME:
            results.extend(_list_flat(item["id"], _path=item_path))
        else:
            results.append({"id": item["id"], "name": item["name"], "path": item_path})
    return results


def fetch_file(file_id: str) -> bytes:
    """Download a file from Google Drive by file ID."""
    return requests.get(f"{DRIVE_API}/files/{file_id}?alt=media").content
