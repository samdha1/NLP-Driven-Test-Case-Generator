from transformers import AutoTokenizer

def load_tokenizer(model_id="meta-llama/Llama-3.2-3B-Instruct"):
    """Loads the Llama-specific tokenizer."""
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer