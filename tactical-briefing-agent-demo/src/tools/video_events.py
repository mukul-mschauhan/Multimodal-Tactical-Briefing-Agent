from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

from src.config import settings
from src.schemas import Entities, Event
from src.tools.evidence import create_thumbnail

VEHICLE_CLASSES = {"car", "bus", "truck", "motorcycle"}
PERSON_CLASS = "person"
ALLOWED_CLASSES = VEHICLE_CLASSES | {PERSON_CLASS}
MODEL = YOLO("yolov8n.pt")


def _in_rect(point: Tuple[float, float], rect: Tuple[float, float, float, float], w: int, h: int) -> bool:
    x1, y1, x2, y2 = rect
    return (x1 * w) <= point[0] <= (x2 * w) and (y1 * h) <= point[1] <= (y2 * h)


def _centroid(box):
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def extract_video_events(video_path: Path, zone_a_rect: Optional[Tuple[float, float, float, float]] = None) -> List[Event]:
    zone_rect = zone_a_rect or tuple(float(x) for x in settings.zone_a_rect.split(","))
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    sample_every = max(1, int(fps / max(settings.frame_sample_fps, 1)))

    events: List[Event] = []
    frame_idx = 0
    prev_vehicle_centroids: Dict[int, Tuple[float, float]] = {}
    stationary_counter: Dict[int, int] = {}
    prev_person_count = 0
    recent_counts = deque(maxlen=8)

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % sample_every != 0:
            frame_idx += 1
            continue

        ts = frame_idx / fps
        h, w = frame.shape[:2]
        results = MODEL.predict(frame, verbose=False)

        person_count = 0
        vehicle_count = 0
        detections = []

        for r in results:
            if r.boxes is None:
                continue
            for box, cls_id in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.cls.cpu().numpy()):
                cls_name = MODEL.names[int(cls_id)]
                if cls_name not in ALLOWED_CLASSES:
                    continue
                c = _centroid(box)
                detections.append((cls_name, c, box))
                if cls_name == PERSON_CLASS:
                    person_count += 1
                elif cls_name in VEHICLE_CLASSES:
                    vehicle_count += 1

        # naive tracking for vehicle_stop
        vehicle_dets = [(i, d) for i, d in enumerate(detections) if d[0] in VEHICLE_CLASSES]
        for i, (_, c, _) in vehicle_dets:
            prev = prev_vehicle_centroids.get(i)
            if prev:
                dist = np.hypot(c[0] - prev[0], c[1] - prev[1])
                stationary_counter[i] = stationary_counter.get(i, 0) + 1 if dist < 8 else 0
                if stationary_counter[i] > settings.frame_sample_fps * 6:
                    event = Event(
                        ts_start=max(0, ts - 6),
                        ts_end=ts,
                        source="video",
                        event_type="vehicle_stop",
                        summary="A vehicle appears stationary for multiple seconds.",
                        entities=Entities(person_count=person_count, vehicle_count=vehicle_count),
                        confidence=0.72,
                        evidence={
                            "video": {
                                "video_file": video_path.name,
                                "timecode_sec": ts,
                                "frame_path": "",
                            }
                        },
                    )
                    event.evidence["video"]["frame_path"] = create_thumbnail(frame, event.event_id)
                    events.append(event)
                    stationary_counter[i] = 0
            prev_vehicle_centroids[i] = c

        # crowd_increase
        recent_counts.append(person_count)
        if len(recent_counts) >= 4 and person_count - min(recent_counts) >= 3:
            event = Event(
                ts_start=max(0, ts - 3),
                ts_end=ts,
                source="video",
                event_type="crowd_increase",
                summary="Observed increase in visible people count.",
                entities=Entities(person_count=person_count, vehicle_count=vehicle_count),
                confidence=0.68,
                evidence={"video": {"video_file": video_path.name, "timecode_sec": ts, "frame_path": ""}},
            )
            event.evidence["video"]["frame_path"] = create_thumbnail(frame, event.event_id)
            events.append(event)
            recent_counts.clear()

        # perimeter_entry
        for cls_name, c, _ in detections:
            if cls_name == PERSON_CLASS and _in_rect(c, zone_rect, w, h):
                event = Event(
                    ts_start=ts,
                    ts_end=ts,
                    source="video",
                    event_type="perimeter_entry",
                    summary="A person entered predefined Zone A.",
                    entities=Entities(person_count=person_count, vehicle_count=vehicle_count),
                    location_tag="Zone A",
                    confidence=0.61,
                    evidence={"video": {"video_file": video_path.name, "timecode_sec": ts, "frame_path": ""}},
                )
                event.evidence["video"]["frame_path"] = create_thumbnail(frame, event.event_id)
                events.append(event)
                break

        # anomaly_motion by sudden count change
        if abs(person_count - prev_person_count) >= 4:
            event = Event(
                ts_start=max(0, ts - 1),
                ts_end=ts,
                source="video",
                event_type="anomaly_motion",
                summary="Sudden change observed in movement/count profile.",
                entities=Entities(person_count=person_count, vehicle_count=vehicle_count),
                confidence=0.57,
                evidence={"video": {"video_file": video_path.name, "timecode_sec": ts, "frame_path": ""}},
            )
            event.evidence["video"]["frame_path"] = create_thumbnail(frame, event.event_id)
            events.append(event)

        prev_person_count = person_count
        frame_idx += 1

    cap.release()
    return events
