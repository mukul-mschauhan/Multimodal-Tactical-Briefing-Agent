from __future__ import annotations

from pathlib import Path
from typing import List

from src.schemas import Event
from src.tools.video_events import extract_video_events


def run_vision(video_files: List[Path]) -> List[Event]:
    events: List[Event] = []
    for path in video_files:
        events.extend(extract_video_events(path))
    return events
