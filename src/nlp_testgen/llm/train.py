from datasets import load_dataset
from transformers import Trainer, TrainingArguments

def train_model(model, tokenizer):
    # Load your formatted text file
    dataset = load_dataset("json", data_files="train_data.jsonl", split="train")

    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True)

    tokenized_dataset = dataset.map(tokenize_function, batched=True)

    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=3,
        per_device_train_batch_size=1, # Keep small for 6GB VRAM
        gradient_accumulation_steps=4, 
        save_steps=100,
        logging_steps=10,
        learning_rate=2e-4,
        fp16=True # Use mixed precision for your RTX 3050
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
    )
    
    trainer.train()
