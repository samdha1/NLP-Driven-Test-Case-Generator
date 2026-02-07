"""
LLM-based specification parser
"""

import json
import re
import logging
from generate import generate_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpecParser:
    """Parse specifications using LLM."""
    
    def __init__(self, model_name="meta-llama/Llama-3.2-1B-Instruct"):
        self.model_name = model_name
    
    def parse(self, text):
        """
        Parse requirement using LLM.
        
        Args:
            text (str): Natural language requirement
            
        Returns:
            dict: Parsed specification
        """
        logger.info(f"Parsing requirement with LLM: {text}")
        
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a requirement analyzer. Extract constraints from the text.
Return ONLY valid JSON with these keys: "min", "max", "data_type", "constraints"

Rules:
- Use integers for min/max if present
- Use null if missing
- data_type: "integer", "float", "string", "boolean"
- constraints: array of additional rules (e.g., ["divisible_by_2", "even_only"])

Example output:
{{"min": 18, "max": 65, "data_type": "integer", "constraints": []}}

Do not include explanation, ONLY the JSON object.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Requirement: {text}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
{{"""

        try:
            response = generate_text(prompt, model_name=self.model_name, max_tokens=150)
            spec = self._extract_json(response)
            
            if spec:
                spec["raw"] = text
                logger.info(f"Successfully parsed: {spec}")
                return spec
            else:
                raise ValueError("Could not parse LLM response")
                
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            raise RuntimeError(f"Failed to parse requirement: {e}")
    
    def _extract_json(self, response):
        """Extract JSON from LLM response."""
        try:
            # Remove markdown
            cleaned = re.sub(r'```json\s*|\s*```', '', response)
            cleaned = cleaned.strip()
            
            # Find JSON object
            json_match = re.search(r'\{[^}]+\}', cleaned)
            if json_match:
                return json.loads(json_match.group(0))
            
            return json.loads(cleaned)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None