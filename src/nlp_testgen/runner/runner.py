"""
Test runner: run target script with test input (argv or stdin).
"""

import subprocess


def run_test_stdin(target_script: str, stdin_content: str, timeout: int = 5) -> dict:
    """
    Run target script with stdin_content fed to stdin (e.g. multi-line input).
    Returns dict: input (preview), status ("Pass" / "Fail" / "Timeout" / "Error"), output, error.
    """
    try:
        result = subprocess.run(
            ["python", target_script],
            input=stdin_content,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "input": stdin_content[:200] + ("..." if len(stdin_content) > 200 else ""),
            "status": "Pass" if result.returncode == 0 else "Fail",
            "output": (result.stdout or "").strip(),
            "error": (result.stderr or "").strip(),
        }
    except subprocess.TimeoutExpired:
        return {"input": stdin_content[:200], "status": "Timeout", "output": "", "error": "Execution timed out"}
    except Exception as e:
        return {"input": stdin_content[:200], "status": "Error", "output": "", "error": str(e)}


def run_test(target_script, test_input):
    """Run a test case against target program."""
    try:
        input_str = str(test_input) if test_input is not None else ""
        
        result = subprocess.run(
            ['python', target_script, input_str],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return {
            "input": test_input,
            "status": "Pass" if result.returncode == 0 else "Fail",
            "output": (result.stdout or "").strip(),
            "error": (result.stderr or "").strip(),
        }
        
    except subprocess.TimeoutExpired:
        return {"input": test_input, "status": "Timeout", "output": "", "error": "Timed out"}
    except Exception as e:
        return {"input": test_input, "status": "Error", "output": "", "error": str(e)}


def run_tests(target_script: str, test_cases: list) -> list:
    """
    Run a list of test cases against the target script.
    Each test case: dict with "input" key (and optionally "type", "label").
    Returns list of result dicts with input, status, output, error (and type, label if present).
    """
    results = []
    for tc in test_cases:
        inp = tc.get("input") if isinstance(tc, dict) else tc
        res = run_test(target_script, inp)
        if isinstance(tc, dict):
            res["type"] = tc.get("type", "")
            res["label"] = tc.get("label", "")
            res["category"] = tc.get("category", "")
            res["severity"] = tc.get("severity", "")
        results.append(res)
    return results