from __future__ import annotations

from pathlib import Path
import re
from typing import List

from src.schemas import Entities, Event

TIMESTAMP_RE = re.compile(r"\[(\d{2}):(\d{2}):(\d{2})\]\s*(.*)")
KEYWORDS = {
    "stopped": "vehicle_stop",
    "crowd": "crowd_increase",
    "congestion": "anomaly_motion",
    "camera feed": "monitoring_update",
    "monitor": "monitoring_update",
}


def _to_sec(h: str, m: str, s: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s)


def extract_transcript_events(path: Path) -> List[Event]:
    events: List[Event] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, start=1):
        m = TIMESTAMP_RE.match(line.strip())
        if not m:
            continue
        ts = _to_sec(m.group(1), m.group(2), m.group(3))
        content = m.group(4)
        lower = content.lower()
        for kw, event_type in KEYWORDS.items():
            if kw in lower:
                confidence = 0.8 if kw in {"stopped", "crowd", "congestion"} else 0.6
                events.append(
                    Event(
                        ts_start=ts,
                        ts_end=ts,
                        source="transcript",
                        event_type=event_type,
                        summary=f"Transcript noted: {content[:90]}",
                        entities=Entities(),
                        confidence=confidence,
                        evidence={
                            "transcript": {
                                "file": path.name,
                                "line_numbers": [i],
                                "excerpt": content,
                            }
                        },
                    )
                )
                break
    return events
