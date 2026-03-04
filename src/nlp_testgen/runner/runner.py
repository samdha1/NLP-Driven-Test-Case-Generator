"""
Test runner
"""

import subprocess


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
            "status": " Pass" if result.returncode == 0 else " Fail",
            "output": result.stdout.strip(),
            "error": result.stderr.strip()
        }
        
    except subprocess.TimeoutExpired:
        return {"input": test_input, "status": " Timeout"}
    except Exception as e:
        return {"input": test_input, "status": f" Error: {e}"}