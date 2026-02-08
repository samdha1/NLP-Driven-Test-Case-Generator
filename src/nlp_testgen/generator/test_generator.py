"""
LLM-based test case generator
"""

import logging
from  nlp_testgen.llm.generate import generate_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestGenerator:
    """Generate test cases using LLM."""
    
    def __init__(self, model_name="meta-llama/Llama-3.2-3B-Instruct"):
        self.model_name = model_name
    
    def generate_test_cases(self, parsed_spec, test_type="all"):
        """
        Generate test cases using LLM.
        
        Args:
            parsed_spec (dict): Parsed specification
            test_type (str): Type of tests to generate
            
        Returns:
            str: Generated test cases
        """
        requirement = parsed_spec.get("raw", "")
        min_val = parsed_spec.get("min", "N/A")
        max_val = parsed_spec.get("max", "N/A")
        
        # Simple, direct prompt
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a QA engineer. Generate 8 test cases for this requirement.

For each test, write:
Test N: Input = X, Expected = accept/reject, Reason = why

Be concise and clear.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Requirement: {requirement}
Range: {min_val} to {max_val}

Generate tests:<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
Test 1:"""

        logger.info("Generating test cases with LLM...")
        
        try:
            response = generate_text(
                prompt,
                model_name=self.model_name,
                max_tokens=400,
                temperature=0.7
            )
            
            # Add "Test 1:" prefix since we removed it from prompt
            full_response = "Test 1:" + response
            
            logger.info("Test cases generated successfully")
            return full_response
            
        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            # Return simple fallback tests
            return self._generate_fallback_tests(parsed_spec)
    
    def _generate_fallback_tests(self, spec):
        """Generate simple tests without LLM."""
        min_val = spec.get("min")
        max_val = spec.get("max")
        
        if min_val and max_val:
            tests = f"""
Test 1: Input = {min_val - 1}, Expected = reject, Reason = below minimum
Test 2: Input = {min_val}, Expected = accept, Reason = at minimum
Test 3: Input = {(min_val + max_val) // 2}, Expected = accept, Reason = middle value
Test 4: Input = {max_val}, Expected = accept, Reason = at maximum
Test 5: Input = {max_val + 1}, Expected = reject, Reason = above maximum
Test 6: Input = 0, Expected = reject, Reason = zero edge case
Test 7: Input = -1, Expected = reject, Reason = negative value
Test 8: Input = 99999, Expected = reject, Reason = extremely large value
"""
            return tests.strip()
        else:
            return "Error: Could not generate tests - no min/max values found"