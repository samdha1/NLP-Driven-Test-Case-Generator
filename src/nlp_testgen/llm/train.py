from transformers import Trainer, TrainingArguments

def train_model(model, tokenizer, dataset):
    """
    Starter function for fine-tuning the model on your specific
    test-case datasets.
    """
    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=100,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )
    
    trainer.train()