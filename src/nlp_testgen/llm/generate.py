import urllib.request
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model(model_name="llama3.2"):
    """
    Mock function to maintain compatibility.
    Ollama handles models internally via the API.
    """
    logger.info(f"Ollama will be used for model: {model_name}")
    return None, None, "cpu"


def generate_text(prompt, model_name="llama3.2", max_tokens=400, temperature=0.7):
    """
    Generate text using local Ollama API.
    Ensure Ollama is running and the model (e.g., llama3.2) is pulled.
    """
    # Auto-adjust HF specific model names to Ollama equivalent
    if model_name == "meta-llama/Llama-3.2-3B-Instruct" or "llama" in model_name.lower():
        model_name = "llama3.2"
        
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model_name,
        "prompt": prompt,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        },
        "stream": False
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "").strip()
    except Exception as e:
        logger.error(f"Error generating text with Ollama API: {e}. Is Ollama running?")
        return ""


def clear_cache():
    """
    Mock function to maintain compatibility.
    """
    logger.info("Cache clearing is handled by Ollama server.")