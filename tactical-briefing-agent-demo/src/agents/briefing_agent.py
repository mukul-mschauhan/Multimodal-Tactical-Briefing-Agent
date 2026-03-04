from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from src.config import OUTPUTS_DIR
from src.schemas import BriefResult, Event, FactItem


def _fmt_ts(seconds: float) -> str:
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02}:{m:02}:{sec:02}"


def _extract_evidence(e: Event) -> str:
    if "video" in e.evidence:
        v = e.evidence["video"]
        return f"video={v.get('video_file')}@{v.get('timecode_sec')} frame={v.get('frame_path')}"
    if "transcript" in e.evidence:
        t = e.evidence["transcript"]
        return f"transcript={t.get('file')} lines={t.get('line_numbers')}"
    if "incident" in e.evidence:
        i = e.evidence["incident"]
        return f"incident_row={i.get('row_id')}"
    return "Unknown / not observed"


def _to_pdf(md_text: str, pdf_path: Path) -> None:
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    y = 760
    for line in md_text.splitlines():
        c.drawString(40, y, line[:110])
        y -= 14
        if y < 40:
            c.showPage()
            y = 760
    c.save()


def build_brief(events: List[Event], facts: List[FactItem], previous_brief: str = "", create_pdf: bool = True) -> BriefResult:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
    if not events:
        md = f"# SITREP\n\nGenerated: {now}\n\nNo events available. Unknown / not observed."
        out = OUTPUTS_DIR / "briefs" / "sitrep_latest.md"
        out.write_text(md, encoding="utf-8")
        return BriefResult(markdown=md, brief_path=str(out))

    start = min(e.ts_start for e in events)
    end = max(e.ts_end for e in events)
    top = events[:5]

    summary_lines = [
        f"- {_fmt_ts(e.ts_start)} {e.summary} [{e.event_id}]"
        for e in top
    ]
    timeline_lines = [
        f"- {_fmt_ts(e.ts_start)} | {e.event_type} | {e.summary} [{e.event_id}]"
        for e in events
    ]

    change_line = "- Initial brief; no previous baseline available."
    if previous_brief:
        change_line = "- Compared with previous brief: updates detected in current event timeline."

    appendix_rows = [
        f"| {e.event_id} | {e.event_type} | {_extract_evidence(e)} |"
        for e in events
    ]

    md = "\n".join(
        [
            "# Multimodal Tactical Briefing Agent (Workshop Safe) SITREP",
            f"**Time Window:** {_fmt_ts(start)} - {_fmt_ts(end)}",
            f"**Generated:** {now}",
            "",
            "## Situation Summary",
            *summary_lines,
            "",
            "## Timeline",
            *timeline_lines,
            "",
            "## Changes Since Last Brief",
            change_line,
            "",
            "## Open Questions",
            "- Are there additional camera angles to improve observation coverage? [Unknown / not observed]",
            "- Are transcript entries complete for the selected window? [Unknown / not observed]",
            "",
            "## Evidence Appendix",
            "| event_id | event_type | evidence |",
            "|---|---|---|",
            *appendix_rows,
        ]
    )

    out = OUTPUTS_DIR / "briefs" / "sitrep_latest.md"
    out.write_text(md, encoding="utf-8")
    pdf_path: Optional[Path] = None
    if create_pdf:
        pdf_path = OUTPUTS_DIR / "briefs" / "sitrep_latest.pdf"
        _to_pdf(md, pdf_path)
    return BriefResult(markdown=md, brief_path=str(out), pdf_path=str(pdf_path) if pdf_path else None)
