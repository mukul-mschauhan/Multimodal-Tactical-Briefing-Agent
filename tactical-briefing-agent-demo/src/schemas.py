from __future__ import annotations

from typing import Dict, List, Literal, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

SourceType = Literal["video", "transcript", "incident"]
LocationTag = Literal["Zone A", "Zone B", "Zone C"]


class Entities(BaseModel):
    person_count: int = 0
    vehicle_count: int = 0


class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    ts_start: float
    ts_end: float
    source: SourceType
    event_type: str
    summary: str
    entities: Entities = Field(default_factory=Entities)
    location_tag: LocationTag = "Zone B"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: Dict = Field(default_factory=dict)


class FactItem(BaseModel):
    timestamp: float
    statement: str
    event_ids: List[str]


class BriefResult(BaseModel):
    markdown: str
    brief_path: str
    pdf_path: Optional[str] = None
