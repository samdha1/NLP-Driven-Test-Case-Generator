import json
import re
import logging
from nlp_testgen.llm.generate import generate_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpecParser:
    def __init__(self, model_name="meta-llama/Llama-3.2-3B-Instruct"):
        self.model_name = model_name

    def parse(self, text):
        logger.info(f"Parsing requirement with LLM: {text}")

        if self.multiple(text):
            logger.info("Multiple inputs detected — parsing each separately")
            return self._parse_multiple(text)
        return self.single(text)
    
    def single(self, text):
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a requirement analyst. Extract the validation logic from the provided text.
1. Identify the 'min' and 'max' numerical bounds.
2. If only one bound exists (e.g., "at least 18"), set the other to null.
3. Identify the 'data_type' (integer, float, or string).
4. List any additional 'constraints' (e.g., "must be even", "no special characters").

Return ONLY a valid JSON object.
Format: {{"min": number/null, "max": number/null, "data_type": "string", "constraints": ["list"]}}
No explanation, no code blocks.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Text: {text}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

        try:
            response = generate_text(prompt, model_name=self.model_name, max_tokens=100)
            logger.info(f"LLM response: {response}")
            spec = self._extract_json(response)

            if spec:
                spec["raw"] = text
                logger.info(f"Successfully parsed: {spec}")
                return spec
            else:
                logger.warning("JSON extraction failed, using regex fallback")
                return self._regex_fallback(text)

        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return self._regex_fallback(text)

    def multiple(self, text):
        separators = [r',\s*\w+\s+(must|should|between|from)', r';\s*\w+', r'\.\s+[A-Z]\w+']
        for sep in separators:
            if re.search(sep, text):
                return True
        range_count = len(re.findall(
            r'(between\s+\d+\s+and\s+\d+|\d+\s+to\s+\d+|\d+\s*-\s*\d+)',
            text.lower()
        ))
        return range_count > 1

    def spliting(self, text):
        segments = re.split(r'(?<=[^0-9]),\s*(?=[a-zA-Z])|;\s*(?=[a-zA-Z])', text)
        segments = [s.strip() for s in segments if len(s.strip()) > 5]
        logger.info(f"Split into {len(segments)} segments: {segments}")
        return segments

    def _parse_multiple(self, text):
        segments = self.spliting(text)

        if len(segments) <= 1:
            return self.single(text)

        specs = []
        for segment in segments:
            logger.info(f"Parsing segment: {segment}")
            spec = self.single(segment)
            spec["field"] = self._extract_field_name(segment)
            specs.append(spec)

        return specs

    def _extract_field_name(self, segment):
        match = re.match(r'^([A-Za-z][A-Za-z0-9_ ]{1,20}?)\s+(must|should|between|from|is)', segment, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return segment.split()[0] if segment else "field"

    def _extract_json(self, response):
        try:
            json_pattern = r'\{\s*"min"\s*:\s*\d+\s*,\s*"max"\s*:\s*\d+[^}]*\}'
            match = re.search(json_pattern, response)

            if match:
                json_str = match.group(0)
                logger.info(f"Extracted JSON: {json_str}")
                return json.loads(json_str)
            match = re.search(r'\{[^}]+\}', response)
            if match:
                json_str = match.group(0)
                logger.info(f"Found JSON: {json_str}")
                return json.loads(json_str)

            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed: {e}")
            logger.error(f"Response was: {response}")
            return None

    def _regex_fallback(self, text):
        logger.info("Using regex fallback parser")
        spec = {
            "min": None,
            "max": None,
            "data_type": "integer",
            "constraints": [],
            "raw": text
        }
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