from nlp_testgen.llm.generate import generate_text

# This will use the GPT-2 model configured in src/nlp_testgen/llm/model.py
print("Loading model and generating response... (This may take a moment)")
result = generate_text("List security risks for a web form input.")

print("\n--- AI Generated Security Risks ---")
print(result)