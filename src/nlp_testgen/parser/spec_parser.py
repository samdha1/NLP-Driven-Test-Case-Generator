"""
LLM-based specification parser with better error handling
"""

import json
import re
import logging
from nlp_testgen.llm.generate import generate_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpecParser:
    """Parse specifications using LLM."""
    
    def __init__(self, model_name="meta-llama/Llama-3.2-3B-Instruct"):
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
Extract min and max values from the text.
Return ONLY a JSON object, nothing else.
Format: {{"min": number, "max": number, "data_type": "integer"}}
No explanation, no code blocks, just the JSON.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Text: {text}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

        try:
            response = generate_text(prompt, model_name=self.model_name, max_tokens=100)
            logger.info(f"LLM response: {response}")
            
            spec = self._extract_json(response)
            
            if spec:
                spec["raw"] = text
                spec["constraints"] = []
                logger.info(f"Successfully parsed: {spec}")
                return spec
            else:
                # Fallback: extract numbers with regex
                logger.warning("JSON extraction failed, using regex fallback")
                return self._regex_fallback(text)
                
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return self._regex_fallback(text)
    
    def _extract_json(self, response):
        """Extract JSON from LLM response - handles messy output."""
        try:
            # Remove everything except the JSON object
            # Look for pattern like {"min": 2, "max": 5, ...}
            json_pattern = r'\{\s*"min"\s*:\s*\d+\s*,\s*"max"\s*:\s*\d+[^}]*\}'
            match = re.search(json_pattern, response)
            
            if match:
                json_str = match.group(0)
                logger.info(f"Extracted JSON: {json_str}")
                return json.loads(json_str)
            
            # Try to find any JSON object
            match = re.search(r'\{[^}]+\}', response)
            if match:
                json_str = match.group(0)
                logger.info(f"Found JSON: {json_str}")
                return json.loads(json_str)
            
            # Try to parse the whole thing
            return json.loads(response.strip())
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed: {e}")
            logger.error(f"Response was: {response}")
            return None
    
    def _regex_fallback(self, text):
        """Fallback parser using regex when LLM fails."""
        logger.info("Using regex fallback parser")
        
        spec = {
            "min": None,
            "max": None,
            "data_type": "integer",
            "constraints": [],
            "raw": text
        }
        
        # Look for "between X and Y" or "X and Y" patterns
        patterns = [
            r'between\s+(\d+)\s+and\s+(\d+)',
            r'(\d+)\s+and\s+(\d+)',
            r'(\d+)\s+to\s+(\d+)',
            r'(\d+)\s*-\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                spec["min"] = int(match.group(1))
                spec["max"] = int(match.group(2))
                logger.info(f"Regex found: min={spec['min']}, max={spec['max']}")
                return spec
        
        logger.warning("Could not extract min/max from text")
        return spec