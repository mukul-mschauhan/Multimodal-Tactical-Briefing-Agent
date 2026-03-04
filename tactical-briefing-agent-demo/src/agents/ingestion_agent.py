from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from src.config import INPUTS_DIR


def run_ingestion(time_window_minutes: int) -> Dict[str, List[Path]]:
    videos = sorted((INPUTS_DIR / "video").glob("*.mp4"))
    transcripts = sorted((INPUTS_DIR / "transcripts").glob("*.txt"))
    incidents = sorted((INPUTS_DIR / "incidents").glob("*.csv"))
    return {
        "video_files": videos,
        "transcript_files": transcripts,
        "incident_files": incidents,
        "time_window_minutes": time_window_minutes,
    }
