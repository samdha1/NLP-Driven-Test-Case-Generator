import re

class SpecParser:
    def __init__(self):
        # Basic patterns to identify types and constraints
        self.patterns = {
            "range": r"between (\d+) and (\d+)",
            "type": r"(integer|string|boolean|float)",
            "mandatory": r"(must|required|mandatory)"
        }

    def parse(self, text):
        """
        Parses NL text into a simplified specification dictionary.
        """
        spec = {"raw": text, "constraints": []}
        
        # Example: Extracting range
        range_match = re.search(self.patterns["range"], text.lower())
        if range_match:
            spec["min"] = int(range_match.group(1))
            spec["max"] = int(range_match.group(2))
            spec["constraints"].append("range_limit")

        # Example: Extracting type
        type_match = re.search(self.patterns["type"], text.lower())
        if type_match:
            spec["data_type"] = type_match.group(1)
            
        return spec