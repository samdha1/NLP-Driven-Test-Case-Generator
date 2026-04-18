"""
Z3 Solver Engine: Numerical constraints from structured JSON spec → precise logic values.
Produces boundary/edge values for formal verification and boundary testing.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    z3 = None


def _solve_constraints(spec: Dict[str, Any]) -> List[Any]:
    """Use Z3 to find values satisfying constraints (e.g. even, divisible by N)."""
    if not Z3_AVAILABLE or z3 is None:
        return []
    min_val = spec.get("min")
    max_val = spec.get("max")
    data_type = (spec.get("data_type") or "integer").lower()
    constraints_list = spec.get("constraints") or []
    if min_val is None and max_val is None:
        return []

    if data_type == "integer" and (min_val is not None or max_val is not None):
        x = z3.Int("x")
        conds = []
        if min_val is not None:
            conds.append(x >= min_val)
        if max_val is not None:
            conds.append(x <= max_val)
        # Parse constraints like "even", "divisible by 2", "odd"
        for c in constraints_list:
            cstr = (c if isinstance(c, str) else str(c)).lower()
            if "even" in cstr:
                conds.append(x % 2 == 0)
            elif "odd" in cstr:
                conds.append(x % 2 == 1)
            elif "divisible" in cstr or "divisible by" in cstr:
                import re
                m = re.search(r"divisible\s+by\s*(\d+)", cstr) or re.search(r"by\s*(\d+)", cstr)
                if m:
                    d = int(m.group(1))
                    if d:
                        conds.append(x % d == 0)
        if not conds:
            return []
        solver = z3.Solver()
        solver.add(conds)
        results = []
        for _ in range(5):  # get a few distinct models
            if solver.check() != z3.sat:
                break
            m = solver.model()
            v = m.eval(x).as_long()
            results.append(v)
            solver.add(x != v)
        return results
    return []


def get_precise_logic_values(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    From structured JSON spec, produce precise logic values (boundary + constraint-satisfying).
    Returns list of {"value": ..., "label": str, "type": "boundary"|"constraint"}.
    """
    out: List[Dict[str, Any]] = []
    min_val = spec.get("min")
    max_val = spec.get("max")
    data_type = (spec.get("data_type") or "integer").lower()

    if data_type == "integer":
        if min_val is not None:
            try:
                mn = int(min_val)
                out.append({"value": mn - 1, "label": "just_below_min", "type": "boundary"})
                out.append({"value": mn, "label": "at_min", "type": "boundary"})
                out.append({"value": mn + 1, "label": "just_above_min", "type": "boundary"})
            except (TypeError, ValueError):
                pass
        if max_val is not None:
            try:
                mx = int(max_val)
                out.append({"value": mx - 1, "label": "just_below_max", "type": "boundary"})
                out.append({"value": mx, "label": "at_max", "type": "boundary"})
                out.append({"value": mx + 1, "label": "just_above_max", "type": "boundary"})
            except (TypeError, ValueError):
                pass
        if min_val is not None and max_val is not None:
            try:
                mn, mx = int(min_val), int(max_val)
                mid = (mn + mx) // 2
                out.append({"value": mid, "label": "mid_range", "type": "boundary"})
            except (TypeError, ValueError):
                pass
        # Z3-derived constraint values
        for v in _solve_constraints(spec):
            out.append({"value": v, "label": "constraint_satisfying", "type": "constraint"})
    elif data_type == "float":
        if min_val is not None:
            try:
                mn = float(min_val)
                out.append({"value": mn - 0.01, "label": "just_below_min", "type": "boundary"})
                out.append({"value": mn, "label": "at_min", "type": "boundary"})
                out.append({"value": mn + 0.01, "label": "just_above_min", "type": "boundary"})
            except (TypeError, ValueError):
                pass
        if max_val is not None:
            try:
                mx = float(max_val)
                out.append({"value": mx - 0.01, "label": "just_below_max", "type": "boundary"})
                out.append({"value": mx, "label": "at_max", "type": "boundary"})
                out.append({"value": mx + 0.01, "label": "just_above_max", "type": "boundary"})
            except (TypeError, ValueError):
                pass
    # string: length bounds if present in constraints
    elif data_type == "string":
        length_min = length_max = None
        for c in (spec.get("constraints") or []):
            cstr = (c if isinstance(c, str) else str(c)).lower()
            if "length" in cstr or "character" in cstr:
                import re
                m = re.search(r"(\d+)\s*-\s*(\d+)", cstr) or re.search(r"(\d+)\s+to\s+(\d+)", cstr)
                if m:
                    length_min, length_max = int(m.group(1)), int(m.group(2))
                m = re.search(r"at least\s*(\d+)", cstr)
                if m:
                    length_min = int(m.group(1))
                m = re.search(r"(\d+)\s*-\s*(\d+)", cstr)
                if m and not length_min:
                    length_min, length_max = int(m.group(1)), int(m.group(2))
        if length_min is not None:
            out.append({"value": "x" * (length_min - 1), "label": "below_min_length", "type": "boundary"})
            out.append({"value": "x" * length_min, "label": "at_min_length", "type": "boundary"})
        if length_max is not None:
            out.append({"value": "x" * length_max, "label": "at_max_length", "type": "boundary"})
            out.append({"value": "x" * (length_max + 1), "label": "above_max_length", "type": "boundary"})
        if length_min is None and length_max is None:
            out.append({"value": "", "label": "empty_string", "type": "boundary"})
            out.append({"value": "a", "label": "single_char", "type": "boundary"})

    # Deduplicate by value (keep first label/type)
    seen = set()
    unique = []
    for item in out:
        v = item["value"]
        if v not in seen:
            seen.add(v)
            unique.append(item)
    logger.info(f"Z3 engine produced {len(unique)} precise logic values")
    return unique
