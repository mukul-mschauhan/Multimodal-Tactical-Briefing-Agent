from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List

DENYLIST = {
    "intercept",
    "attack",
    "ambush",
    "evade",
    "route",
    "target",
    "vulnerability",
    "identify",
    "identification",
    "face recognition",
}

REWRITE_MAP = {
    "deploy units": "Request additional camera coverage and neutral monitoring updates.",
    "pursue": "Request continued observation and reporting of observable changes.",
}


@dataclass
class PolicyResult:
    text: str
    blocked_terms: List[str]


def enforce_policy(text: str) -> PolicyResult:
    lowered = text.lower()
    blocked = sorted([term for term in DENYLIST if term in lowered])

    safe = text
    for src, dst in REWRITE_MAP.items():
        safe = re.sub(src, dst, safe, flags=re.IGNORECASE)

    # force no weapon inference
    safe = re.sub(r"(?i)weapon\s*assessment\s*:\s*.*", "Weapon assessment: Not assessed", safe)

    if blocked:
        lines = []
        for line in safe.splitlines():
            l = line.lower()
            if any(term in l for term in blocked):
                lines.append("- Content removed by safety policy. Unknown / not observed.")
            else:
                lines.append(line)
        safe = "\n".join(lines)

    return PolicyResult(text=safe, blocked_terms=blocked)


def ensure_grounded_lines(lines: Iterable[str]) -> List[str]:
    grounded = []
    for line in lines:
        if not line.strip():
            continue
        if "[" in line and "event_" in line:
            grounded.append(line)
        elif "[" in line and "-" in line and "]" in line:
            grounded.append(line)
        else:
            grounded.append(f"{line} Unknown / not observed.")
    return grounded
