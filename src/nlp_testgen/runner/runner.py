import subprocess

def run_test(target_script, test_input):
    """
    Runs the target program with the generated input and checks for crashes.
    """
    try:
        # Assuming the target takes input via stdin or arguments
        result = subprocess.run(
            ['python', target_script, str(test_input)],
            capture_output=True, text=True, timeout=5
        )
        return {
            "status": "Success" if result.returncode == 0 else "Failed",
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {"status": "Crash/Error", "error": str(e)}