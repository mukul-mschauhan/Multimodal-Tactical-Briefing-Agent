from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from src.schemas import Entities, Event


def _parse_ts(value: str) -> float:
    try:
        parts = value.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except Exception:
        pass
    return 0.0


def extract_incident_events(path: Path) -> List[Event]:
    df = pd.read_csv(path)
    events: List[Event] = []
    for idx, row in df.iterrows():
        note = str(row.get("note", ""))
        events.append(
            Event(
                ts_start=_parse_ts(str(row.get("timestamp", "00:00:00"))),
                ts_end=_parse_ts(str(row.get("timestamp", "00:00:00"))),
                source="incident",
                event_type=str(row.get("category", "incident_note")).strip().lower().replace(" ", "_"),
                summary=f"Incident note: {note[:90]}",
                entities=Entities(),
                confidence=0.7,
                evidence={"incident": {"row_id": int(idx)}},
            )
        )
    return events
