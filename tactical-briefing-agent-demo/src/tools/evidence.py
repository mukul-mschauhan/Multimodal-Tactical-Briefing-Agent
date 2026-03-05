from __future__ import annotations

from pathlib import Path
import cv2

from src.config import OUTPUTS_DIR


def extract_frame_at_time(video_path: Path, timecode_sec: float):
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_idx = int(timecode_sec * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ok, frame = cap.read()
    cap.release()
    return frame if ok else None


def create_thumbnail(frame, event_id: str, max_w: int = 480) -> str:
    if frame is None:
        return ""
    h, w = frame.shape[:2]
    scale = min(1.0, max_w / max(w, 1))
    thumb = cv2.resize(frame, (int(w * scale), int(h * scale)))
    out = OUTPUTS_DIR / "frames" / f"{event_id}_thumb.jpg"
    cv2.imwrite(str(out), thumb)
    return relative_output_path(out)


def relative_output_path(path: Path) -> str:
    return str(path.relative_to(OUTPUTS_DIR.parent))
