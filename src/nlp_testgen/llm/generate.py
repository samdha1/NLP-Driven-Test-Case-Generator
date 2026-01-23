from nlp_testgen.llm.model import load_model
from nlp_testgen.llm.tokenizer import load_tokenizer

def generate_text(prompt, model_name="meta-llama/Llama-3.2-3B-Instruct"):
    model, device = load_model(model_name)
    tokenizer = load_tokenizer(model_name)
    
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    output_tokens = model.generate(
        **inputs, 
        max_new_tokens=300, 
        do_sample=True, 
        temperature=0.7,
        top_k=50,
        pad_token_id=tokenizer.eos_token_id
    )
    
    # This ensures only the AI's new text is returned, not the prompt
    new_tokens = output_tokens[0][len(inputs["input_ids"][0]):]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)
