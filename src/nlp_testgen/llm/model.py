from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

def load_model(model_id="meta-llama/Llama-3.2-3B-Instruct"):
    """Optimized loading for 6GB RTX 3050 using 4-bit quantization."""
    # Check for GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Configuration to compress the model to fit in 6GB VRAM
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto" # Automatically place model on GPU
    )
    return model, device