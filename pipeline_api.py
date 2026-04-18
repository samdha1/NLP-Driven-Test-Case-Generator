"""
Single pipeline: parse any requirement (simple or complex) → unified spec → test cases.
Optional: run tests against user code and return pass/fail.
"""

import os
import sys
import tempfile

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
_src = os.path.join(_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


def run_pipeline(requirement: str, code: str = None, target_script: str = None):
    """
    Parse requirement (auto-detects simple vs complex) → one spec → one list of test cases.
    If `code` is provided, run tests against it (temp file). If `target_script` path is provided, run against that file. Returns run_results when either is set.
    """
    try:
        from src.nlp_testgen.complex.complex_spec import parse_requirement, generate_test_cases
        from src.nlp_testgen.runner.runner import run_test, run_test_stdin
    except Exception:
        from nlp_testgen.complex.complex_spec import parse_requirement, generate_test_cases
        from nlp_testgen.runner.runner import run_test, run_test_stdin

    spec = parse_requirement(requirement)
    if not spec:
        return {"spec": None, "test_cases": [], "error": "Could not parse requirement"}

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

    return out
