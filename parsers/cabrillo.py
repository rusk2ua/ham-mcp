def parse(data: bytes) -> list[dict]:
    """Parse a Cabrillo contest log and return QSO records.

    Note: Cabrillo QSO field positions vary by contest (ARRL DX, CQ WW,
    Field Day, etc.). Adjust field indices below for your specific contest.
    The layout here matches the common 10-column format.
    """
    qsos = []
    for line in data.decode("utf-8", errors="replace").splitlines():
        if not line.startswith("QSO:"):
            continue
        parts = line.split()
        if len(parts) < 9:
            continue
        qsos.append({
            "raw": line,
            "freq": parts[1],
            "mode": parts[2],
            "date": parts[3],
            "time": parts[4],
            "sent_call": parts[5],
            "sent_rst": parts[6],
            "sent_exch": parts[7],
            "rcvd_call": parts[8],
            "rcvd_rst": parts[9] if len(parts) > 9 else "",
            "rcvd_exch": parts[10] if len(parts) > 10 else "",
        })
    return qsos
