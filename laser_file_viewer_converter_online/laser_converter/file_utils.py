from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path


def safe_filename(name: str) -> str:
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    stem = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+", "_", stem).strip("_") or "archivo"
    return f"{stem}{suffix}"


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return f"{num_bytes} B"


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def append_history(history_csv: str | Path, row: dict) -> None:
    history_csv = Path(history_csv)
    history_csv.parent.mkdir(parents=True, exist_ok=True)
    exists = history_csv.exists()
    fieldnames = [
        "timestamp",
        "input_file",
        "input_format",
        "output_file",
        "output_format",
        "status",
        "message",
    ]
    with history_csv.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in fieldnames})
