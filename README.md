# NLP-Driven Test Case Generator

NLP-Driven Test Case Generator is an automated tool designed to bridge the gap between Natural Language (NL) software requirements and rigorous testing. It uses traditional parsing for boundary value analysis and leverages Large Language Models (LLMs)—specifically **Llama-3.2-3B**—to identify high-risk security vulnerabilities.

## 🚀 Features

* **Requirement Parsing**: Automatically extracts data types (integer, string, boolean, float) and numerical constraints from natural language text.
* **Boundary Value Analysis**: Generates test cases for exact bounds, as well as "off-by-one" values (just above and just below limits).
* **LLM Security Audits**: Utilizes Llama-3.2-3B to identify risks such as Buffer Overflows, SQL Injection, and Integer Overflows based on software requirements.
* **GPU Optimization**: Configured to run efficiently on 6GB VRAM hardware (like the RTX 3050) using 4-bit quantization.
* **Automated Runner**: Includes a module to execute generated tests against target applications and capture success, failure, or system crashes.

## 🛠️ Installation

Ensure you have Python 3.10 or higher installed.

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/your-username/nlp_testgen.git](https://github.com/your-username/nlp_testgen.git)
   cd nlp_testgen
Install the package and dependencies:

Bash

pip install .
Dependencies include: torch, transformers, numpy, spacy, and tokenizers.

💻 Usage
Automated Security Audit
Run the specialized security script to analyze a requirement using Llama-3.2:

Bash

python llama_security_test.py
CLI Boundary Generation
Generate standard boundary test cases directly from the command line:

Bash

nlp_testgen --spec "The application accepts a user_id string between 5 and 10 characters."
AI Risk Analysis
Generate general security risks for web inputs using the built-in AI module:

Bash

python test_ai.py
📂 Project Structure
src/nlp_testgen/parser/: Extracts constraints and types from NL.

src/nlp_testgen/generator/: Logic for calculating boundary test values.

src/nlp_testgen/llm/: Model loading, quantization, and text generation logic.

src/nlp_testgen/runner/: Executes tests and monitors for program crashes.

examples/: Sample programs to test the generator against.

📄 License
Refer to the LICENSE file in the root directory for details.