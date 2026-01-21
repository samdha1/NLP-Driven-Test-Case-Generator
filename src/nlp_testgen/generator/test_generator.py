import random

class TestGenerator:
    def generate_boundary_cases(self, parsed_spec):
        test_cases = []
        
        if "min" in parsed_spec and "max" in parsed_spec:
            low = parsed_spec["min"]
            high = parsed_spec["max"]
            
            # Boundary Logic: just below, exactly, and just above limits
            test_cases.append({"val": low - 1, "desc": "Below lower bound"})
            test_cases.append({"val": low, "desc": "Exact lower bound"})
            test_cases.append({"val": high, "desc": "Exact upper bound"})
            test_cases.append({"val": high + 1, "desc": "Above upper bound"})
            
        return test_cases