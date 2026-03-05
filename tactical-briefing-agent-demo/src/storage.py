from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, List

from src.config import OUTPUTS_DIR
from src.schemas import Event

DB_PATH = OUTPUTS_DIR / "logs" / "events.db"
AUDIT_LOG_PATH = OUTPUTS_DIR / "logs" / "events_audit.jsonl"


def init_db() -> None:
    OUTPUTS_DIR.joinpath("logs").mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                ts_start REAL,
                ts_end REAL,
                source TEXT,
                event_type TEXT,
                summary TEXT,
                entities_json TEXT,
                location_tag TEXT,
                confidence REAL,
                evidence_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS briefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                brief_path TEXT,
                markdown TEXT
            )
            """
        )


def persist_events(events: Iterable[Event]) -> None:
    records = list(events)
    if not records:
        return
    with sqlite3.connect(DB_PATH) as conn:
        for e in records:
            conn.execute(
                """
                INSERT OR REPLACE INTO events (
                    event_id, ts_start, ts_end, source, event_type, summary,
                    entities_json, location_tag, confidence, evidence_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    e.event_id,
                    e.ts_start,
                    e.ts_end,
                    e.source,
                    e.event_type,
                    e.summary,
                    e.entities.model_dump_json(),
                    e.location_tag,
                    e.confidence,
                    json.dumps(e.evidence),
                ),
            )
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        for e in records:
            f.write(e.model_dump_json() + "\n")


def persist_brief(brief_path: Path | str, markdown: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO briefs (brief_path, markdown) VALUES (?, ?)",
            (str(brief_path), markdown),
        )


def fetch_last_brief() -> str:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT markdown FROM briefs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else ""


def load_events() -> List[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT event_id, ts_start, ts_end, source, event_type, summary, location_tag, confidence FROM events ORDER BY ts_start"
        )
        return [
            {
                "event_id": r[0],
                "ts_start": r[1],
                "ts_end": r[2],
                "source": r[3],
                "event_type": r[4],
                "summary": r[5],
                "location_tag": r[6],
                "confidence": r[7],
            }
            for r in cur.fetchall()
        ]
