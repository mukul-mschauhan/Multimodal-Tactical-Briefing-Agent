from __future__ import annotations

from pathlib import Path
from typing import List

from src.schemas import Event
from src.tools.incident_events import extract_incident_events


def run_incident(incident_files: List[Path]) -> List[Event]:
    events: List[Event] = []
    for path in incident_files:
        events.extend(extract_incident_events(path))
    return events
