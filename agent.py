"""
Agentic AI Router — Uses Llama 3.2 (via Ollama) to classify user requirements
and route them to the appropriate project.

Projects:
  - ShivTeja (Streamlit)  → data structures, passwords, logins, file uploads
  - NLP TestGen (Flask)   → complex constraints, boundary analysis, security vectors
"""

import json
import re
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Project definitions ---
PROJECTS = {
    "shivteja": {
        "name": "Shiv Teja",
        "description": "Rule-based NLP test case generator using spaCy compiler pipeline",
        "url": "http://localhost:8501",
        "capabilities": [
            "Data structures: array, stack, queue, linked list, heap, tree, graph",
            "Operations: push, pop, enqueue, dequeue, insert, delete, sort, reverse, max, min, sum, size, length",
            "Authentication: login, password validation",
            "File operations: upload, file type validation",
            "Security risk detection: SQL injection, XSS, unauthorized access, file upload attack, code tampering",
            "Spell checking via SpellChecker",
            "Green computing metrics via CodeCarbon",
            "Execution time analysis per compiler stage",
        ],
    },
    "nlp_testgen": {
        "name": "Sameer",
        "description": "LLM-powered test generator with Z3 solver and security engine",
        "url": "http://localhost:5000",
        "capabilities": [
            "Numeric constraint parsing: 'age between 18 and 60'",
            "Complex multi-variable requirements",
            "Boundary value analysis via Z3 solver",
            "80+ security attack vectors (SQLi, XSS, SSTI, etc.)",
            "LLM-powered requirement parsing",
            "Code execution and test running",
            "Analytics dashboard with charts",
        ],
    },
}

# --- Keywords for fallback classification ---
SHIVTEJA_KEYWORDS = [
    "stack", "queue", "array", "linked list", "tree", "graph", "heap",
    "push", "pop", "enqueue", "dequeue", "insert", "delete", "remove",
    "max", "min", "sum", "reverse", "sort", "size", "length",
    "password", "login", "upload", "file", "security",
    "admin", "script", "database", "malicious", "attack",
]


def classify_with_llm(requirement: str) -> dict:
    """
    Use Llama 3.2 via Ollama to classify which project should handle the requirement.
    Returns: {"project": "shivteja"|"nlp_testgen", "confidence": float, "reason": str}
    """
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an AI router that decides which project should handle a user's software testing requirement.

PROJECT_A name: "shivteja" (Shiv Teja)
- Rule-based NLP test case generator using a strict compiler pipeline.
- ONLY handles explicit data structure commands (e.g., 'push 5 to stack', 'max in array') or simple auth/file checks.
- If the requirement is a complex algorithmic problem, a Codeforces/Leetcode question, or a math puzzle, DO NOT CHOOSE THIS.

PROJECT_B name: "nlp_testgen" (Sameer)  
- LLM-powered test generator with Z3 constraint solver and automated execution.
- Best for: Codeforces/Leetcode problems, algorithm constraints ("circular table", "players"), numeric bounds, complex multi-variable specs, and boundary value analysis.
- DEFAULT to this project for any general or complex software requirement.

Given the user's requirement, decide which project handles it best.
Reply with ONLY valid JSON (no markdown, no explanation):
{{"project": "shivteja" or "nlp_testgen", "confidence": 0.0 to 1.0, "reason": "one line explanation"}}<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{requirement}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3.2",
        "prompt": prompt,
        "options": {"temperature": 0.1, "num_predict": 150},
        "stream": False,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            raw = result.get("response", "").strip()
            logger.info(f"LLM raw response: {raw}")
            return _parse_classification(raw)
    except Exception as e:
        logger.warning(f"LLM classification failed: {e}, using keyword fallback")
        return classify_with_keywords(requirement)


def _parse_classification(raw: str) -> dict:
    """Parse the LLM's JSON response, with fallback handling."""
    try:
        # Try direct JSON parse
        obj = json.loads(raw)
        if isinstance(obj, dict) and "project" in obj:
            proj = obj["project"].lower().strip()
            if proj not in ("shivteja", "nlp_testgen"):
                proj = "nlp_testgen"
            return {
                "project": proj,
                "confidence": float(obj.get("confidence", 0.8)),
                "reason": obj.get("reason", "LLM classification"),
            }
    except (json.JSONDecodeError, TypeError):
        pass

    # Try to find JSON in the response
    match = re.search(r'\{[^{}]*"project"[^{}]*\}', raw)
    if match:
        try:
            obj = json.loads(match.group(0))
            proj = obj.get("project", "nlp_testgen").lower().strip()
            if proj not in ("shivteja", "nlp_testgen"):
                proj = "nlp_testgen"
            return {
                "project": proj,
                "confidence": float(obj.get("confidence", 0.7)),
                "reason": obj.get("reason", "LLM classification"),
            }
        except (json.JSONDecodeError, TypeError):
            pass

    # Check for project name mentions
    lower = raw.lower()
    if "shivteja" in lower:
        return {"project": "shivteja", "confidence": 0.6, "reason": "LLM mentioned shivteja"}
    return {"project": "nlp_testgen", "confidence": 0.5, "reason": "Default routing"}


def classify_with_keywords(requirement: str) -> dict:
    """Fallback: keyword-based classification when Ollama is unavailable."""
    req_lower = requirement.lower()
    matches = sum(1 for kw in SHIVTEJA_KEYWORDS if re.search(r'\b' + re.escape(kw) + r'\b', req_lower))
    if matches >= 1:
        return {
            "project": "shivteja",
            "confidence": min(0.5 + matches * 0.1, 0.95),
            "reason": f"Keyword match ({matches} keywords detected: data structure / auth / file operation)",
        }
    return {
        "project": "nlp_testgen",
        "confidence": 0.7,
        "reason": "No specific data structure / auth keywords found; routing to LLM-powered generator",
    }


def classify(requirement: str) -> dict:
    """
    Main classification entry point. Tries LLM first, falls back to keywords.
    Returns: {"project": str, "confidence": float, "reason": str, "url": str, "project_name": str}
    """
    result = classify_with_llm(requirement)
    proj_info = PROJECTS[result["project"]]
    result["url"] = proj_info["url"]
    result["project_name"] = proj_info["name"]
    result["project_description"] = proj_info["description"]
    return result


if __name__ == "__main__":
    # Quick test
    tests = [
        "push 5 elements into stack",
        "find max element in array",
        "age between 18 and 60",
        "validate password strength",
        "given an array of n integers, 1 <= n <= 10^5",
        "insert element in linked list",
        "username must be a string between 3 and 20 characters",
    ]
    for t in tests:
        r = classify(t)
        print(f"  [{r['project']:12s}] ({r['confidence']:.1f}) {t}")
        print(f"    → {r['reason']}")
