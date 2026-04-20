"""
Test Case Aggregator: Combines Precise Logic Values (Z3) + Creative Security Strings (LLM)
into a single list of runnable test cases with type, label, category, and severity.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def aggregate_test_cases(
    precise_logic_values: List[Dict[str, Any]],
    creative_security_strings: List[Dict[str, Any]],
    dedupe: bool = True,
) -> List[Dict[str, Any]]:
    """
    Merge Z3 output and LLM security output into unified test cases.
    Each item: {"input": value, "type": "boundary"|"constraint"|"security",
                "label": str, "category": str, "severity": str}.
    """
    out: List[Dict[str, Any]] = []
    for item in precise_logic_values:
        out.append({
            "input": item.get("value"),
            "type": item.get("type", "boundary"),
            "label": item.get("label", ""),
            "category": "logic",
            "severity": "info",
        })
    for item in creative_security_strings:
        out.append({
            "input": item.get("value"),
            "type": "security",
            "label": item.get("label", "security"),
            "category": item.get("category", "security"),
            "severity": item.get("severity", "high"),
        })
    if dedupe:
        seen = set()
        unique = []
        for tc in out:
            key = (tc["input"], tc["type"])
            if key not in seen:
                seen.add(key)
                unique.append(tc)
        out = unique
    logger.info(f"Aggregator produced {len(out)} test cases")
    return out
