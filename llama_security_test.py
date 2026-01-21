import torch
from nlp_testgen.llm.generate import generate_text

def print_gpu_status():
    """Verifies RTX 3050 6GB usage."""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        print(f"\n[GPU INFO] Device: {torch.cuda.get_device_name(0)}")
        print(f"[GPU INFO] VRAM Allocated: {allocated:.2f} GB")
        print(f"[GPU INFO] VRAM Reserved: {reserved:.2f} GB")

def run_security_audit(requirement):
    # Llama-3 specific prompt format for better instruction following
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert Security Engineer. Your task is to identify 3 high-risk 
boundary test cases for the following software requirement. 
Focus on Buffer Overflows, SQL Injection, and Integer Overflows.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Requirement: {requirement}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

    print(f"\n--- Analyzing Requirement: {requirement} ---")
    print("Loading Llama-3.2-3B on GPU...")
    
    # This calls the updated model.py logic
    response = generate_text(prompt, model_name="meta-llama/Llama-3.2-3B-Instruct")
    
    print("\n--- LLM GENERATED SECURITY TEST CASES ---")
    print(response)
    print_gpu_status()

if __name__ == "__main__":
    test_req = "The application accepts a 'user_id' string between 5 and 10 characters."
    run_security_audit(test_req)