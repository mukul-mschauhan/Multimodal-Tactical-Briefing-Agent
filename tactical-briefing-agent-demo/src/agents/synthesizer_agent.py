from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from src.schemas import Event, FactItem


def run_synthesizer(events: List[Event]) -> Tuple[List[Event], List[FactItem]]:
    ordered = sorted(events, key=lambda e: e.ts_start)
    by_type: Dict[str, List[Event]] = defaultdict(list)
    all_events = list(ordered)

    for e in ordered:
        by_type[e.event_type].append(e)

    for _, items in by_type.items():
        for i in range(1, len(items)):
            prev, cur = items[i - 1], items[i]
            if abs(cur.ts_start - prev.ts_start) <= 90:
                if abs(cur.entities.person_count - prev.entities.person_count) >= 3:
                    discrepancy = Event(
                        ts_start=min(prev.ts_start, cur.ts_start),
                        ts_end=max(prev.ts_end, cur.ts_end),
                        source="incident",
                        event_type="discrepancy",
                        summary=f"Discrepancy detected between sources for {cur.event_type}.",
                        entities=cur.entities,
                        confidence=0.55,
                        evidence={"incident": {"row_id": -1, "related_event_ids": [prev.event_id, cur.event_id]}},
                    )
                    all_events.append(discrepancy)

    facts = [
        FactItem(
            timestamp=e.ts_start,
            statement=f"{e.summary} (source={e.source}, type={e.event_type})",
            event_ids=[e.event_id],
        )
        for e in sorted(all_events, key=lambda e: e.ts_start)
    ]
    return sorted(all_events, key=lambda e: e.ts_start), facts
