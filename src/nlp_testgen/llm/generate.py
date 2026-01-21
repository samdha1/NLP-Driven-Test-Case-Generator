from nlp_testgen.llm.model import load_model
from nlp_testgen.llm.tokenizer import load_tokenizer

def generate_text(prompt, model_name="gpt2"):
    model, device = load_model(model_name)
    tokenizer = load_tokenizer(model_name)
    
    # Move inputs to your RTX 3050 (device='cuda')
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    output_tokens = model.generate(
        **inputs, 
        max_new_tokens=256, # Increased for more detailed security cases
        do_sample=True, 
        top_k=50,
        pad_token_id=tokenizer.eos_token_id # Fixes the warning in your screenshot
    )
    
    # This line ensures it only returns the assistant's answer, not the prompt
    new_tokens = output_tokens[0][len(inputs["input_ids"][0]):]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)