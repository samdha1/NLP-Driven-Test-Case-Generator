import torch
from nlp_testgen.llm.generate import generate_text

def run_dynamic_audit(requirement):
    """Generates test cases based on the tone of the user input."""
    
    # Check if the user is asking for security or general logic
    is_security = any(word in requirement.lower() for word in ["security", "risk", "attack", "overflow", "sql"])
    
    if is_security:
        role = "Expert Security Engineer"
        focus = "Buffer Overflows, SQL Injection, and Integer Overflows"
    else:
        role = "Senior QA Engineer"
        focus = "Boundary values, logic errors, and unexpected input types"

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an {role}. Generate 5 diverse and critical test cases for the following software requirement. 
Focus on: {focus}.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Requirement: {requirement}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

    print(f"\n[AI] Analyzing as {role}...")
    response = generate_text(prompt, model_name="meta-llama/Llama-3.2-3B-Instruct")
    
    print("\n--- GENERATED TEST CASES ---")
    print(response)

if __name__ == "__main__":
    print("NLP-Driven Test Case Generator (RTX 3050 Optimized)")
    print("Type 'exit' to stop.")
    
    while True:
        user_req = input("\nEnter your English problem/requirement: ")
        if user_req.lower() == 'exit':
            break
        
        if user_req.strip():
            run_dynamic_audit(user_req)
