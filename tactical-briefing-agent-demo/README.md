# Multimodal Tactical Briefing Agent (Workshop Safe)

A complete Python laptop demo showing multi-agent orchestration for **safe, evidence-grounded situational reporting**.

## What this demo does

- Ingests public video clips (`inputs/video/*.mp4`), synthetic transcripts (`inputs/transcripts/*.txt`), and incident notes (`inputs/incidents/incidents.csv`).
- Extracts structured events into a shared Event Bus schema.
- Orchestrates specialized agents with LangGraph.
- Produces a workshop-safe SITREP markdown report (plus optional PDF export).
- Stores full event history in SQLite and JSONL audit logs.

## Hard safety guardrails implemented

- **No tactical/operational advice** (policy denylist + rewrite + action removal).
- **No identification** (no face recognition, no person identification).
- **No weapon inference** (`Weapon assessment: Not assessed`).
- **Evidence grounding required** (claims include `event_id`; unsupported claims become `Unknown / not observed.`).
- **Policy Agent required** before final output persistence.

## Repo layout

```text
tactical-briefing-agent-demo/
  inputs/
    video/
    transcripts/
    incidents/
  outputs/
    frames/
    briefs/
    logs/
  src/
    tools/
    agents/
    ui/
```

## Quickstart

```bash
cd tactical-briefing-agent-demo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/ui/app.py
```

## Workshop run flow

1. Drop one or more `.mp4` clips in `inputs/video/`.
2. Add transcript text files in `inputs/transcripts/` using this format:
   - `[10:02:05] Unit B: One vehicle stopped unusually for ~30 seconds.`
3. Update `inputs/incidents/incidents.csv` (`timestamp,category,note`).
4. In Streamlit sidebar, choose inputs + time window and click **Run Briefing Graph**.
5. Review:
   - Event table + audit data
   - Evidence thumbnails
   - SITREP markdown preview
   - Downloadable markdown/PDF brief

## Architecture summary

- **Tools**
  - `video_events.py`: frame sampling + YOLOv8n detections + heuristic event extraction
  - `transcript_events.py`: timestamp/keyword extraction
  - `incident_events.py`: CSV parsing into events
  - `evidence.py`: frame extraction + thumbnails + relative links

- **Agents**
  - `Ingestion Agent`: discovers files
  - `Vision Agent`: video events
  - `Comms Agent`: transcript events
  - `Incident Agent`: incident CSV events
  - `Synthesizer Agent`: timeline merge + discrepancy detection
  - `Briefing Agent`: SITREP template writer
  - `Policy Agent`: denylist filtering + safe rewriting + guardrail enforcement

- **Persistence**
  - SQLite (`outputs/logs/events.db`)
  - JSONL audit log (`outputs/logs/events_audit.jsonl`)

## Notes

- YOLO model defaults to `yolov8n` for laptop speed and auto-downloads on first run.
- LLM usage is optional; the default summarization path is local/rule-based.
- The app is designed for workshop demonstrations and safety-first discussion.
