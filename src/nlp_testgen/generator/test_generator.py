"""
LLM-based test case generator
"""

import logging
from generate import generate_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestGenerator:
    """Generate test cases using LLM."""
    
    def __init__(self, model_name="meta-llama/Llama-3.2-1B-Instruct"):
        self.model_name = model_name
    
    def generate_test_cases(self, parsed_spec, test_type="all"):
        """
        Generate test cases using LLM.
        
        Args:
            parsed_spec (dict): Parsed specification
            test_type (str): "boundary", "security", "edge", or "all"
            
        Returns:
            list: Test cases
        """
        requirement = parsed_spec.get("raw", "")
        
        # Detect if security-focused
        security_keywords = ["security", "password", "auth", "login", "sql", "injection"]
        is_security = any(word in requirement.lower() for word in security_keywords)
        
        if test_type == "security" or is_security:
            focus = "Security vulnerabilities: SQL injection, XSS, buffer overflow, integer overflow, authentication bypass"
            role = "Expert Security Engineer"
        elif test_type == "boundary":
            focus = "Boundary value analysis: minimum, maximum, just below/above limits"
            role = "QA Test Engineer"
        elif test_type == "edge":
            focus = "Edge cases: null, zero, negative, extreme values, type mismatches"
            role = "QA Test Engineer"
        else:  # all
            focus = "Comprehensive testing: boundary values, edge cases, and security vulnerabilities"
            role = "Senior QA and Security Engineer"
        
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a {role}. Generate exactly 10 diverse test cases for the requirement.

For each test case, provide:
- Test number
- Input value
- Expected result (accept/reject)
- Reason why this test is important

Focus: {focus}

Format each test clearly and concisely.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Requirement: {requirement}

Parsed constraints:
- Min: {parsed_spec.get('min', 'N/A')}
- Max: {parsed_spec.get('max', 'N/A')}
- Type: {parsed_spec.get('data_type', 'N/A')}
- Additional: {parsed_spec.get('constraints', [])}

Generate test cases:<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

        logger.info(f"Generating {test_type} test cases with LLM...")
        
        try:
            response = generate_text(
                prompt,
                model_name=self.model_name,
                max_tokens=500,
                temperature=0.7
            )
            
            logger.info("Test cases generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            raise RuntimeError(f"Failed to generate tests: {e}")