from __future__ import annotations

from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.briefing_agent import build_brief
from src.agents.comms_agent import run_comms
from src.agents.incident_agent import run_incident
from src.agents.ingestion_agent import run_ingestion
from src.agents.policy_agent import enforce_policy
from src.agents.synthesizer_agent import run_synthesizer
from src.agents.vision_agent import run_vision
from src.config import ensure_dirs
from src.schemas import Event
from src.storage import fetch_last_brief, init_db, persist_brief, persist_events


class GraphState(TypedDict, total=False):
    time_window_minutes: int
    video_files: list
    transcript_files: list
    incident_files: list
    vision_events: List[Event]
    comms_events: List[Event]
    incident_events: List[Event]
    all_events: List[Event]
    facts: list
    brief_markdown: str
    brief_path: str
    pdf_path: str
    blocked_terms: list
    errors: list


def _safe(state: GraphState, fn, key: str) -> Dict[str, Any]:
    try:
        return {key: fn()}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"{key}: {e}"]}


def ingest_node(state: GraphState) -> Dict[str, Any]:
    return run_ingestion(state.get("time_window_minutes", 15))


def vision_node(state: GraphState) -> Dict[str, Any]:
    return _safe(state, lambda: run_vision(state.get("video_files", [])), "vision_events")


def comms_node(state: GraphState) -> Dict[str, Any]:
    return _safe(state, lambda: run_comms(state.get("transcript_files", [])), "comms_events")


def incident_node(state: GraphState) -> Dict[str, Any]:
    return _safe(state, lambda: run_incident(state.get("incident_files", [])), "incident_events")


def synth_node(state: GraphState) -> Dict[str, Any]:
    events = state.get("vision_events", []) + state.get("comms_events", []) + state.get("incident_events", [])
    merged, facts = run_synthesizer(events)
    return {"all_events": merged, "facts": facts}


def policy_node(state: GraphState) -> Dict[str, Any]:
    brief = state.get("brief_markdown", "")
    result = enforce_policy(brief)
    return {"brief_markdown": result.text, "blocked_terms": result.blocked_terms}


def brief_node(state: GraphState) -> Dict[str, Any]:
    prior = fetch_last_brief()
    result = build_brief(state.get("all_events", []), state.get("facts", []), previous_brief=prior, create_pdf=True)
    return {"brief_markdown": result.markdown, "brief_path": result.brief_path, "pdf_path": result.pdf_path or ""}


def persist_node(state: GraphState) -> Dict[str, Any]:
    persist_events(state.get("all_events", []))
    if state.get("brief_path"):
        persist_brief(state.get("brief_path"), state.get("brief_markdown", ""))
    return {}


def build_graph():
    ensure_dirs()
    init_db()
    graph = StateGraph(GraphState)
    graph.add_node("ingest", ingest_node)
    graph.add_node("vision_extract", vision_node)
    graph.add_node("comms_extract", comms_node)
    graph.add_node("incident_extract", incident_node)
    graph.add_node("synthesize", synth_node)
    graph.add_node("write_brief", brief_node)
    graph.add_node("policy_filter", policy_node)
    graph.add_node("persist_outputs", persist_node)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "vision_extract")
    graph.add_edge("vision_extract", "comms_extract")
    graph.add_edge("comms_extract", "incident_extract")
    graph.add_edge("incident_extract", "synthesize")
    graph.add_edge("synthesize", "write_brief")
    graph.add_edge("write_brief", "policy_filter")
    graph.add_edge("policy_filter", "persist_outputs")
    graph.add_edge("persist_outputs", END)
    return graph.compile()


def run_workflow(time_window_minutes: int = 15) -> GraphState:
    app = build_graph()
    return app.invoke({"time_window_minutes": time_window_minutes, "errors": []})
