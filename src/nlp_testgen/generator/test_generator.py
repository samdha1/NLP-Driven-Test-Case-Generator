import logging
from nlp_testgen.llm.generate import generate_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestGenerator:
    def __init__(self, model_name="meta-llama/Llama-3.2-3B-Instruct"):
        self.model_name = model_name
    
    def generate_test_cases(self, parsed_spec, test_type="all"):
        requirement = parsed_spec.get("raw", "")
        min_val = parsed_spec.get("min", "N/A")
        max_val = parsed_spec.get("max", "N/A")

        if test_type == "boundary":
            focus = (
                "Focus ONLY on boundary value tests:\n"
                "- Just below minimum (min-1)\n"
                "- At minimum (min)\n"
                "- Just above minimum (min+1)\n"
                "- Just below maximum (max-1)\n"
                "- At maximum (max)\n"
                "- Just above maximum (max+1)\n"
            )
        elif test_type == "security":
            focus = (
                "Focus ONLY on security-relevant tests:\n"
                "- SQL injection inputs\n"
                "- XSS / script injection\n"
                "- Buffer overflow / oversized inputs\n"
                "- Null / empty inputs\n"
                "- Special characters and control bytes\n"
                "- Integer overflow / underflow\n"
            )
        elif test_type == "edge":
            focus = (
                "Focus ONLY on edge cases:\n"
                "- Unexpected data types\n"
                "- Floating point when integer expected\n"
                "- Whitespace-only input\n"
                "- Very large or very small values\n"
                "- Zero and negative numbers\n"
            )
        else:  
            focus = (
                "Include:\n"
                "- Positive tests (valid inputs).\n"
                "- Boundary tests (exact limits).\n"
                "- Negative tests (invalid inputs).\n"
                "- Edge cases (unexpected or extreme values).\n"
            )

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert QA Engineer. Generate 10 diverse test cases for the following software requirement.
{focus}
Requirement Context: {requirement}
Parsed Constraints: Min={min_val}, Max={max_val}

Format:
Test N: [Type] | Input = X | Expected = Y | Reason = Z<|eot_id|>
No explanation, no code blocks.<|eot_id|>
...
"""     
        try:
            response = generate_text(
                prompt,
                model_name=self.model_name,
                max_tokens=400,
                temperature=0.7
            )
            full_response = "Test 1:" + response
            
            logger.info("Test cases generated successfully")
            return full_response
            
        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            return self._generate_fallback_tests(parsed_spec)
    
    def _generate_fallback_tests(self, spec):
        min_val = spec.get("min")
        max_val = spec.get("max")
        if min_val and max_val:
            tests = f"""
Test 1: Input = {min_val - 1}, Expected = reject, Reason = below minimum
Test 2: Input = {min_val}, Expected = accept, Reason = at minimum
Test 3: Input = {(min_val + max_val) // 2}, Expected = accept, Reason = middle value
Test 4: Input = {max_val}, Expected = accept, Reason = at maximum
Test 5: Input = {max_val + 1}, Expected = reject, Reason = above maximum
"""
            return tests.strip()
        else:
            return "Error: Could not generate tests - no min/max values found"