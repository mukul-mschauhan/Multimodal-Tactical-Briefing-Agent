from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
INPUTS_DIR = BASE_DIR / "inputs"
OUTPUTS_DIR = BASE_DIR / "outputs"


@dataclass(frozen=True)
class Settings:
    default_time_window_minutes: int = int(os.getenv("DEFAULT_TIME_WINDOW_MINUTES", "15"))
    frame_sample_fps: int = int(os.getenv("FRAME_SAMPLE_FPS", "2"))
    zone_a_rect: str = os.getenv("ZONE_A_RECT", "0.1,0.1,0.5,0.5")
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()


def ensure_dirs() -> None:
    for p in [
        INPUTS_DIR / "video",
        INPUTS_DIR / "transcripts",
        INPUTS_DIR / "incidents",
        OUTPUTS_DIR / "frames",
        OUTPUTS_DIR / "briefs",
        OUTPUTS_DIR / "logs",
    ]:
        p.mkdir(parents=True, exist_ok=True)
