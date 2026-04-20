"""
Single pipeline: parse any requirement (simple or complex) -> unified spec -> test cases.
Optional: run tests against user code and return pass/fail.
Tracks computation time for green computing / CO2 emissions estimation.
"""

import os
import sys
import time
import tempfile

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
_src = os.path.join(_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


# Green computing constants
CPU_POWER_WATTS = 65         # Typical desktop CPU TDP
GPU_POWER_WATTS = 150        # Typical GPU (used by Ollama)
INDIA_CARBON_INTENSITY = 709 # gCO2/kWh (India grid average 2023)
GLOBAL_CARBON_INTENSITY = 475  # gCO2/kWh (global average)
TREES_PER_KG_CO2_YEAR = 21   # One tree absorbs ~21 kg CO2/year


def _estimate_emissions(duration_seconds: float, used_llm: bool = True) -> dict:
    """Estimate energy consumption and CO2 emissions from computation time."""
    power_watts = (CPU_POWER_WATTS + GPU_POWER_WATTS) if used_llm else CPU_POWER_WATTS
    energy_kwh = (power_watts * duration_seconds) / (1000 * 3600)
    co2_grams = energy_kwh * INDIA_CARBON_INTENSITY
    co2_global_grams = energy_kwh * GLOBAL_CARBON_INTENSITY

    # Equivalence metrics
    km_driven = co2_grams / 121  # avg car emits 121 g CO2/km
    phone_charges = energy_kwh / 0.012  # ~12 Wh per phone charge
    led_bulb_seconds = (energy_kwh * 3600 * 1000) / 10  # 10W LED bulb

    return {
        "computation_time_seconds": round(duration_seconds, 2),
        "power_watts": power_watts,
        "energy_kwh": round(energy_kwh, 8),
        "energy_wh": round(energy_kwh * 1000, 4),
        "co2_grams": round(co2_grams, 4),
        "co2_grams_global": round(co2_global_grams, 4),
        "carbon_intensity_used": INDIA_CARBON_INTENSITY,
        "equivalences": {
            "km_driven": round(km_driven, 6),
            "phone_charges": round(phone_charges, 4),
            "led_bulb_seconds": round(led_bulb_seconds, 2),
        },
        "used_llm": used_llm,
    }


def run_pipeline(requirement: str, code: str = None, target_script: str = None):
    """
    Parse requirement (auto-detects simple vs complex) -> one spec -> one list of test cases.
    If `code` is provided, run tests against it (temp file). If `target_script` path is provided, run against that file. Returns run_results when either is set.
    Includes green computing metrics (energy, CO2 emissions).
    """
    pipeline_start = time.time()
    used_llm = False

    try:
        from src.nlp_testgen.complex.complex_spec import parse_requirement, generate_test_cases
        from src.nlp_testgen.runner.runner import run_test, run_test_stdin
    except Exception:
        from nlp_testgen.complex.complex_spec import parse_requirement, generate_test_cases
        from nlp_testgen.runner.runner import run_test, run_test_stdin

    # Check if LLM is available
    try:
        from nlp_testgen.llm.generate import generate_text
        if generate_text:
            used_llm = True
    except Exception:
        pass

    spec = parse_requirement(requirement)
    if not spec:
        elapsed = time.time() - pipeline_start
        return {
            "spec": None,
            "test_cases": [],
            "error": "Could not parse requirement",
            "green_metrics": _estimate_emissions(elapsed, used_llm),
        }

    test_cases = generate_test_cases(spec)
    out = {"spec": spec, "test_cases": test_cases}

    script_path = None
    if code and code.strip():
        try:
            f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
            f.write(code.strip())
            f.close()
            script_path = f.name
        except Exception as e:
            out["run_results"] = []
            out["run_error"] = str(e)
            elapsed = time.time() - pipeline_start
            out["green_metrics"] = _estimate_emissions(elapsed, used_llm)
            return out
    elif target_script and os.path.isfile(target_script):
        script_path = target_script

    if script_path:
        try:
            run_results = []
            for tc in test_cases:
                # Use argv when running against target_script and we have single input (CLI compat); else stdin
                if target_script and "input" in tc and "formatted" in tc and "\n" not in (tc.get("formatted") or ""):
                    res = run_test(script_path, tc.get("input"))
                elif "formatted" in tc:
                    res = run_test_stdin(script_path, tc["formatted"])
                    res["formatted_input"] = (tc["formatted"] or "")[:300] + ("..." if len(tc.get("formatted", "")) > 300 else "")
                else:
                    res = run_test(script_path, tc.get("input"))
                res["type"] = tc.get("type", "")
                res["label"] = tc.get("label", "")
                res["category"] = tc.get("category", "")
                res["severity"] = tc.get("severity", "")
                run_results.append(res)
            out["run_results"] = run_results
        except Exception as e:
            out["run_results"] = []
            out["run_error"] = str(e)
        finally:
            if code and code.strip() and script_path and os.path.isfile(script_path):
                try:
                    os.unlink(script_path)
                except Exception:
                    pass

    elapsed = time.time() - pipeline_start
    out["green_metrics"] = _estimate_emissions(elapsed, used_llm)
    return out
