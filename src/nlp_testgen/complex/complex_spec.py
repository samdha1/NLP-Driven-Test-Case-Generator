"""
Unified spec and test case generation: handles both simple (e.g. "age between 18 and 60")
and complex (LeetCode/Codeforces-style) requirements. One parser, one test generator.
"""

import json
import logging
import random
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from nlp_testgen.llm.generate import generate_text
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False
    generate_text = None


def parse_requirement(problem_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse any requirement into a unified spec with "inputs" array.
    Handles simple ("age between 18 and 60") and complex (arrays, multiple vars).
    Returns e.g. { "inputs": [ {"name": "age", "type": "integer", "min": 18, "max": 60} ], "raw": "..." }
    """
    if LLM_AVAILABLE and generate_text:
        try:
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a requirement analyst. Parse the text into a JSON spec of input variables.
- Simple: "age between 18 and 60" -> {{"inputs": [{{"name": "age", "type": "integer", "min": 18, "max": 60}}]}}
- Complex: multiple vars, arrays -> use type integer, string, array, matrix; add min, max, length_min, length_max, element_type where relevant.
Return ONLY a valid JSON object with key "inputs" (array of objects). No explanation.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{problem_text[:2000]}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""
            response = generate_text(prompt, max_tokens=400, temperature=0.3)
            spec = _extract_complex_spec(response)
            if spec:
                spec["raw"] = problem_text
                return spec
        except Exception as e:
            logger.warning(f"LLM parse failed: {e}")

    return _regex_unified_spec(problem_text)


# Alias for backward compatibility
parse_complex_spec = parse_requirement


def _extract_complex_spec(response: str) -> Optional[Dict[str, Any]]:
    try:
        match = re.search(r'\{[\s\S]*"inputs"[\s\S]*\}', response)
        if match:
            return json.loads(match.group(0))
        return json.loads(response.strip())
    except (json.JSONDecodeError, TypeError):
        return None


def _regex_unified_spec(text: str) -> Dict[str, Any]:
    """Fallback: extract simple (between X and Y) or n/array patterns."""
    spec = {"inputs": [], "raw": text}
    # Simple: "between 18 and 60", "18 to 60", "from 18 to 60"
    simple = re.search(r'(?:between|from)\s+(\d+)\s+(?:and|to)\s+(\d+)|(\d+)\s+to\s+(\d+)|(\d+)\s*-\s*(\d+)', text, re.I)
    if simple:
        g = simple.groups()
        if g[0] is not None:
            a, b = int(g[0]), int(g[1])
        elif g[2] is not None:
            a, b = int(g[2]), int(g[3])
        else:
            a, b = int(g[4]), int(g[5])
        name = "input"
        m = re.search(r'(\w+)\s+(?:must|should|is)?\s*(?:be)?\s*(?:between|from)', text, re.I)
        if m:
            name = m.group(1).strip()
        spec["inputs"].append({"name": name, "type": "integer", "min": min(a, b), "max": max(a, b)})
        return spec
    # n and array
    n_match = re.search(r'n\s*(?:<=?|between)\s*(\d+)\s*(?:and|to|<=?)\s*(\d+)', text, re.I)
    if n_match:
        spec["inputs"].append({
            "name": "n",
            "type": "integer",
            "min": int(n_match.group(1)),
            "max": int(n_match.group(2)),
        })
    if re.search(r'array|list|sequence', text, re.I):
        spec["inputs"].append({
            "name": "arr",
            "type": "array",
            "element_type": "integer",
            "length_min": 1,
            "length_max": int(spec["inputs"][0]["max"]) if spec["inputs"] else 100,
        })
    if not spec["inputs"]:
        spec["inputs"] = [{"name": "input", "type": "integer", "min": 0, "max": 100}]
    return spec


def _is_single_scalar(spec: Dict[str, Any]) -> bool:
    """True if spec has exactly one input and it's integer, float, or string (no array/matrix)."""
    inputs = spec.get("inputs") or []
    if len(inputs) != 1:
        return False
    t = (inputs[0].get("type") or "integer").lower()
    return t in ("integer", "float", "string")


def generate_test_cases(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate test cases from unified spec. Handles both:
    - Single scalar: uses Z3 + security engine (boundary + security), returns list of { input, type, label, formatted }.
    - Multiple or array/matrix: returns list of { inputs, formatted }.
    """
    if _is_single_scalar(spec):
        inp_spec = (spec.get("inputs") or [{}])[0]
        legacy_spec = {
            "min": inp_spec.get("min"),
            "max": inp_spec.get("max"),
            "data_type": inp_spec.get("type", "integer"),
            "constraints": inp_spec.get("constraints", []),
            "raw": spec.get("raw", ""),
        }
        try:
            from src.nlp_testgen.solver.z3_engine import get_precise_logic_values
            from src.nlp_testgen.security.llm_security_engine import get_creative_security_strings
            from src.nlp_testgen.aggregator.aggregator import aggregate_test_cases
        except Exception:
            from nlp_testgen.solver.z3_engine import get_precise_logic_values
            from nlp_testgen.security.llm_security_engine import get_creative_security_strings
            from nlp_testgen.aggregator.aggregator import aggregate_test_cases
        precise = get_precise_logic_values(legacy_spec)
        security = get_creative_security_strings(legacy_spec, max_strings=10)
        aggregated = aggregate_test_cases(precise, security)
        out = []
        for tc in aggregated:
            val = tc.get("input")
            if isinstance(val, str) and len(val) > 500:
                val = val[:500] + "..."
            out.append({
                "input": val,
                "type": tc.get("type", ""),
                "label": tc.get("label", ""),
                "formatted": str(val),
            })
        return out
    return generate_complex_test_cases(spec)


def generate_complex_test_cases(spec: Dict[str, Any], count: int = 8) -> List[Dict[str, Any]]:
    """
    Generate test cases from complex spec. Each case has "inputs" (dict) and "formatted" (multi-line string).
    """
    cases = []
    inputs_spec = spec.get("inputs") or []

    for _ in range(count):
        inp = {}
        lines = []
        for var in inputs_spec:
            name = var.get("name", "x")
            typ = (var.get("type") or "integer").lower()
            if typ == "integer":
                mn = var.get("min", 0)
                mx = var.get("max", 100)
                v = random.randint(mn, mx) if mn <= mx else mn
                inp[name] = v
                lines.append(str(v))
            elif typ == "string":
                length = random.randint(var.get("length_min", 1), min(var.get("length_max", 100), 50))
                inp[name] = "".join(random.choices("abcdef0123456789", k=length))
                lines.append(inp[name])
            elif typ == "array":
                length_min = var.get("length_min", 1)
                length_max = min(var.get("length_max", 20), 50)
                n = random.randint(length_min, length_max) if length_min <= length_max else length_min
                elem_min = var.get("min", var.get("element_min", 0))
                elem_max = var.get("max", var.get("element_max", 100))
                arr = [random.randint(elem_min, elem_max) for _ in range(n)]
                inp[name] = arr
                lines.append(str(n))
                lines.append(" ".join(map(str, arr)))
            elif typ == "matrix":
                rows = random.randint(var.get("rows_min", 1), min(var.get("rows_max", 5), 10))
                cols = random.randint(var.get("cols_min", 1), min(var.get("cols_max", 5), 10))
                matrix = [[random.randint(0, 9) for _ in range(cols)] for _ in range(rows)]
                inp[name] = matrix
                lines.append(f"{rows} {cols}")
                for row in matrix:
                    lines.append(" ".join(map(str, row)))
            else:
                inp[name] = 0
                lines.append("0")
        cases.append({
            "inputs": inp,
            "formatted": "\n".join(lines),
        })
    return cases
