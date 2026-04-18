"""
NLP-Driven Test Case Generator — Entry point.
Single pipeline: requirement → parse (auto simple/complex) → one spec → test cases → optional run.
"""

import json
import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
_src = os.path.join(_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

DEFAULT_TARGET_SCRIPT = os.path.join(_root, "examples", "example_programs.py")


def generate_tests(requirement, test_type="all", target_script=None, run_tests_flag=True):
    try:
        from pipeline_api import run_pipeline

        target_script = target_script or (DEFAULT_TARGET_SCRIPT if os.path.isfile(DEFAULT_TARGET_SCRIPT) else None)
        result = run_pipeline(
            requirement,
            code=None,
            target_script=target_script if run_tests_flag else None,
        )

        print(" NLP-Driven Test Case Generator")
        print("\n Requirement: " + requirement)

        spec = result.get("spec")
        if not spec:
            print("\n Error: " + (result.get("error") or "Could not parse"))
            return
        print("\n Structured JSON Spec:")
        print(json.dumps(spec, indent=2))

        test_cases = result.get("test_cases", [])
        print(f"\n Test cases: {len(test_cases)}")
        for j, tc in enumerate(test_cases[:25], 1):
            if tc.get("formatted") is not None and tc.get("inputs") is not None:
                print(f"   {j}. [complex] " + (tc["formatted"][:80].replace("\n", " | ") + ("…" if len(tc.get("formatted", "")) > 80 else "")))
            else:
                inp = tc.get("input", "")
                typ = tc.get("type", "")
                print(f"   {j}. [{typ}] {inp}")
        if len(test_cases) > 25:
            print(f"   ... and {len(test_cases) - 25} more")

        run_results = result.get("run_results", [])
        if run_results:
            passed = sum(1 for r in run_results if (r.get("status") or "").lower() == "pass")
            print(f"\n Run results: {passed}/{len(run_results)} passed")
            for j, res in enumerate(run_results[:15], 1):
                print(f"   {j}. {res.get('status', '?')}  input: {str(res.get('input', ''))[:50]}")
        print("\n Done.")
    except Exception as e:
        print("\n Error: " + str(e))
        print("  pip install z3-solver  ;  huggingface-cli login  (if using LLM)")


def interactive_mode():
    print(" NLP-Driven Test Case Generator")
    while True:
        try:
            user_input = input("\n Enter requirement (or exit): ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("\n Bye.\n")
                break
            if user_input.lower() == "help":
                print("  Examples: Age between 18 and 60  |  Array of n integers, 1 <= n <= 100")
                continue
            generate_tests(user_input)
        except KeyboardInterrupt:
            print("\n\n Bye.\n")
            break
        except Exception as e:
            print("\n Error: " + str(e) + "\n")


def main():
    if len(sys.argv) > 1:
        generate_tests(" ".join(sys.argv[1:]))
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
