import adif_io


def parse(data: bytes) -> list[dict]:
    """Parse ADIF log data and return a list of QSO records."""
    records, _ = adif_io.read_from_string(data.decode("utf-8", errors="replace"))
    return [dict(r) for r in records]
