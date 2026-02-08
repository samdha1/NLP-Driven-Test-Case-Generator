"""
Text generation using LLM only
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache
_model_cache = {}
_tokenizer_cache = {}


def load_model_and_tokenizer(model_name="meta-llama/Llama-3.2-3B-Instruct"):
    """Load model and tokenizer with caching."""
    
    if model_name in _model_cache:
        logger.info("Using cached model")
        device = "cuda" if next(_model_cache[model_name].parameters()).is_cuda else "cpu"
        return _model_cache[model_name], _tokenizer_cache[model_name], device
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading model {model_name} on {device}")
    
    # Get HuggingFace token
    token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, token=token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model
    if device == "cuda":
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            token=token
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
            token=token
        )
    
    # Cache
    _model_cache[model_name] = model
    _tokenizer_cache[model_name] = tokenizer
    
    logger.info("Model loaded successfully")
    return model, tokenizer, device


def generate_text(prompt, model_name="meta-llama/Llama-3.2-3B-Instruct", max_tokens=300, temperature=0.7):
    """
    Generate text using LLM.
    
    Args:
        prompt (str): Input prompt
        model_name (str): Model to use
        max_tokens (int): Max tokens to generate
        temperature (float): Sampling temperature
        
    Returns:
        str: Generated text
    """
    model, tokenizer, device = load_model_and_tokenizer(model_name)
    
    # Tokenize
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    # Generate
    logger.info("Generating response...")
    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=temperature,
            top_k=50,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    # Decode
    new_tokens = output_tokens[0][len(inputs["input_ids"][0]):]
    generated_text = tokenizer.decode(new_tokens, skip_special_tokens=True)
    
    logger.info("Generation completed")
    return generated_text.strip()


def clear_cache():
    """Clear model cache."""
    global _model_cache, _tokenizer_cache
    _model_cache.clear()
    _tokenizer_cache.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Cache cleared")