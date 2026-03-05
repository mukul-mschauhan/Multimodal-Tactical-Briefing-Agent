from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure `src` package is importable when Streamlit runs this file directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.agents.graph import run_workflow
from src.config import INPUTS_DIR, OUTPUTS_DIR, ensure_dirs
from src.storage import AUDIT_LOG_PATH, DB_PATH, init_db, load_events


def _read_audit_df() -> pd.DataFrame:
    if not AUDIT_LOG_PATH.exists():
        return pd.DataFrame()
    rows = []
    for line in AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return pd.DataFrame(rows)


def main() -> None:
    st.set_page_config(page_title="Multimodal Tactical Briefing Agent (Workshop Safe)", layout="wide")
    ensure_dirs()
    init_db()

    st.sidebar.title("Workshop Controls")
    video_files = sorted(p.name for p in (INPUTS_DIR / "video").glob("*.mp4"))
    transcript_files = sorted(p.name for p in (INPUTS_DIR / "transcripts").glob("*.txt"))
    incident_files = sorted(p.name for p in (INPUTS_DIR / "incidents").glob("*.csv"))

    st.sidebar.multiselect("Videos", options=video_files, default=video_files)
    st.sidebar.multiselect("Transcripts", options=transcript_files, default=transcript_files)
    st.sidebar.multiselect("Incident CSV", options=incident_files, default=incident_files)
    time_window = st.sidebar.slider("Time window (minutes)", 5, 120, 15)

    if st.sidebar.button("Run Briefing Graph"):
        with st.spinner("Running agents..."):
            state = run_workflow(time_window)
        st.session_state["state"] = state

    st.title("Multimodal Tactical Briefing Agent (Workshop Safe)")
    st.caption("Safety-constrained, evidence-grounded SITREP generation demo")

    state = st.session_state.get("state", {})

    events = load_events()
    st.subheader("Key Events")
    st.dataframe(pd.DataFrame(events), use_container_width=True)

    st.subheader("Evidence Thumbnails")
    frames = sorted((OUTPUTS_DIR / "frames").glob("*.jpg"))[-8:]
    cols = st.columns(4)
    for i, frame_path in enumerate(frames):
        with cols[i % 4]:
            st.image(str(frame_path), caption=frame_path.name)

    st.subheader("SITREP Markdown Preview")
    md = state.get("brief_markdown", "No briefing yet. Run graph from sidebar.")
    st.markdown(md)

    brief_path = state.get("brief_path")
    if brief_path and Path(brief_path).exists():
        data = Path(brief_path).read_bytes()
        st.download_button("Download SITREP.md", data=data, file_name="sitrep_latest.md")

    pdf_path = state.get("pdf_path")
    if pdf_path and Path(pdf_path).exists():
        st.download_button("Download SITREP.pdf", data=Path(pdf_path).read_bytes(), file_name="sitrep_latest.pdf")

    st.subheader("Audit Log")
    audit_df = _read_audit_df()
    st.dataframe(audit_df, use_container_width=True)

    st.caption(f"DB: {DB_PATH}")


if __name__ == "__main__":
    main()
