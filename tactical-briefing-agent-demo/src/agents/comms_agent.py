from __future__ import annotations

from pathlib import Path
from typing import List

from src.schemas import Event
from src.tools.transcript_events import extract_transcript_events


def run_comms(transcript_files: List[Path]) -> List[Event]:
    events: List[Event] = []
    for path in transcript_files:
        events.extend(extract_transcript_events(path))
    return events
