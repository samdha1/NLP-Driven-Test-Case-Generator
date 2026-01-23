import json
from nlp_testgen.llm.generate import generate_text

class SpecParser:
    def parse(self, text):
        """
        Uses Llama-3.2-3B to dynamically extract constraints from any English requirement.
        """
        # Prompt designed to get structured data from the LLM
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
        You are a requirement analyzer. Extract numerical bounds and data types from the text.
        Return ONLY a JSON object with keys: "min", "max", "data_type". 
        If a value is missing, use null.<|eot_id|>
        <|start_header_id|>user<|end_header_id|>
        Requirement: {text}<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>"""

        response = generate_text(prompt, model_name="meta-llama/Llama-3.2-3B-Instruct")
        
        try:
            # Attempt to parse the LLM response into a dictionary
            spec = json.loads(response)
        except:
            # Fallback if the LLM output isn't clean JSON
            spec = {"min": None, "max": None, "data_type": "string"}
        
        spec["raw"] = text
        return spec
