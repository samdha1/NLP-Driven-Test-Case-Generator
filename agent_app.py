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

# --- FIX 1: Tightened keyword lists — only SPECIFIC, unambiguous terms for ShivTeja ---
# Generic words like "security", "admin", "database", "attack" were removed
# because they appear in NLP TestGen requirements too and caused wrong routing.

SHIVTEJA_STRONG_KEYWORDS = [
    # Data structure names — very specific
    "stack", "queue", "linked list", "heap", "binary tree", "bst",
    # Explicit DS operations — only meaningful in a DS context
    "push", "pop", "enqueue", "dequeue",
    # Auth / file — ShivTeja-specific features
    "password validation", "login validation", "file upload", "file type",
]

SHIVTEJA_WEAK_KEYWORDS = [
    # These alone are not enough; require 2+ matches to route to ShivTeja
    "array", "insert", "delete", "remove", "sort", "reverse",
    "max element", "min element", "sum of", "size of", "length of",
    "password", "login", "upload",
]

# --- FIX 2: Strong NLP TestGen signals — if any of these appear, always go there ---
NLPTESTGEN_STRONG_KEYWORDS = [
    "between", "boundary", "constraint", "valid range", "invalid range",
    "minimum", "maximum", "1 <=", "<= n", "n <=", "10^",
    "circular", "players", "seats", "leetcode", "codeforces",
    "algorithm", "complexity", "time limit", "space limit",
    "z3", "solver", "multi-variable", "numeric", "integer range",
    "age", "salary", "score", "percentage", "threshold",
]


def classify_with_llm(requirement: str) -> dict:
    """
    Use Llama 3.2 via Ollama to classify which project should handle the requirement.
    Returns: {"project": "shivteja"|"nlp_testgen", "confidence": float, "reason": str}
    """
    # FIX 3: Simplified prompt — removed the complex Llama header format.
    # Using a plain system/user message is more reliable across Ollama model versions.
    prompt = f"""You are an AI router that decides which project handles a software testing requirement.

PROJECT_A: "shivteja"
- ONLY for: simple data structure commands (push/pop/enqueue/dequeue on stack/queue/linked list/heap)
  OR basic password/login/file-upload validation checks.
- NOT for: numeric ranges, boundary analysis, algorithm problems, or multi-variable constraints.

PROJECT_B: "nlp_testgen"
- For: numeric constraints ("age between 18 and 60"), boundary value analysis, complex/multi-variable
  specs, Codeforces/LeetCode style problems, algorithm constraints, and anything not clearly ShivTeja.
- DEFAULT choice when unsure.

Requirement: {requirement}

Reply with ONLY valid JSON, no markdown, no explanation:
{{"project": "shivteja" or "nlp_testgen", "confidence": 0.0 to 1.0, "reason": "one line"}}"""

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
            parsed = _parse_classification(raw)
            # FIX 4: Trust the LLM but override with strong keyword signals
            return _apply_keyword_override(requirement, parsed)
    except Exception as e:
        logger.warning(f"LLM classification failed: {e}, using keyword fallback")
        return classify_with_keywords(requirement)


def _apply_keyword_override(requirement: str, llm_result: dict) -> dict:
    """
    FIX 4: Override LLM decision when there are very strong keyword signals.
    This prevents the LLM from confidently wrong-routing obvious cases.
    """
    req_lower = requirement.lower()

    # If strong NLP TestGen signals exist → always go there
    for kw in NLPTESTGEN_STRONG_KEYWORDS:
        if kw in req_lower:
            if llm_result["project"] != "nlp_testgen":
                logger.info(f"Keyword override → nlp_testgen (matched: '{kw}')")
            return {
                "project": "nlp_testgen",
                "confidence": max(llm_result["confidence"], 0.85),
                "reason": f"Strong NLP TestGen signal detected: '{kw}'",
            }

    # If strong ShivTeja signals exist → go there
    for kw in SHIVTEJA_STRONG_KEYWORDS:
        if kw in req_lower:
            return {
                "project": "shivteja",
                "confidence": max(llm_result["confidence"], 0.85),
                "reason": f"Strong ShivTeja signal detected: '{kw}'",
            }

    return llm_result


def _parse_classification(raw: str) -> dict:
    """Parse the LLM's JSON response, with fallback handling."""
    try:
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

    # Try to extract JSON from mixed text
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

    lower = raw.lower()
    if "shivteja" in lower:
        return {"project": "shivteja", "confidence": 0.6, "reason": "LLM mentioned shivteja"}
    return {"project": "nlp_testgen", "confidence": 0.5, "reason": "Default routing"}


def classify_with_keywords(requirement: str) -> dict:
    """
    FIX 5: Improved keyword fallback — uses separate strong/weak lists with
    a higher threshold, preventing false matches on generic words.
    """
    req_lower = requirement.lower()

    # Check strong NLP TestGen signals first — highest priority
    for kw in NLPTESTGEN_STRONG_KEYWORDS:
        if kw in req_lower:
            return {
                "project": "nlp_testgen",
                "confidence": 0.9,
                "reason": f"Strong NLP TestGen keyword: '{kw}'",
            }

    # Check strong ShivTeja signals
    strong_matches = [kw for kw in SHIVTEJA_STRONG_KEYWORDS
                      if re.search(r'\b' + re.escape(kw) + r'\b', req_lower)]
    if strong_matches:
        return {
            "project": "shivteja",
            "confidence": min(0.7 + len(strong_matches) * 0.1, 0.95),
            "reason": f"Strong ShivTeja keywords: {', '.join(strong_matches)}",
        }

    # Check weak ShivTeja signals — need 2+ matches to avoid false positives
    weak_matches = [kw for kw in SHIVTEJA_WEAK_KEYWORDS
                    if re.search(r'\b' + re.escape(kw) + r'\b', req_lower)]
    if len(weak_matches) >= 2:
        return {
            "project": "shivteja",
            "confidence": min(0.5 + len(weak_matches) * 0.08, 0.85),
            "reason": f"Multiple ShivTeja weak keywords: {', '.join(weak_matches)}",
        }

    # Default to nlp_testgen — it handles the wider range of requirements
    return {
        "project": "nlp_testgen",
        "confidence": 0.75,
        "reason": "No specific ShivTeja keywords found; routing to LLM-powered generator",
    }


def classify(requirement: str) -> dict:
    """
    Main classification entry point. Tries LLM first, falls back to keywords.
    Returns enriched result with URL and project metadata.
    """
    result = classify_with_llm(requirement)
    proj_info = PROJECTS[result["project"]]
    result["url"] = proj_info["url"]
    result["project_name"] = proj_info["name"]
    result["project_description"] = proj_info["description"]
    return result


if __name__ == "__main__":
    tests = [
        ("push 5 elements into stack",              "shivteja"),
        ("find max element in array",               "shivteja"),
        ("pop from queue",                          "shivteja"),
        ("validate password strength",              "shivteja"),
        ("upload a file and check file type",       "shivteja"),
        ("age between 18 and 60",                   "nlp_testgen"),
        ("username must be 3 to 20 characters",     "nlp_testgen"),
        ("given n integers, 1 <= n <= 10^5",        "nlp_testgen"),
        ("circular table with k players",           "nlp_testgen"),
        ("salary must be between 30000 and 150000", "nlp_testgen"),
    ]
    print("\n" + "=" * 70)
    correct = 0
    for req, expected in tests:
        r = classify(req)
        status = "✓" if r["project"] == expected else "✗"
        if r["project"] == expected:
            correct += 1
        print(f"  {status} [{r['project']:12s}] ({r['confidence']:.2f}) {req}")
        print(f"      → {r['reason']}")
    print("=" * 70)
    print(f"  Accuracy: {correct}/{len(tests)}")
    print("=" * 70 + "\n")
