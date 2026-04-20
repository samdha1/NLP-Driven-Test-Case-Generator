# NLP-Driven Test Case Generator

The NLP-Driven Test Case Generator is an automated tool designed to bridge the gap between Natural Language (NL) software requirements and rigorous software testing. The project serves both as an academic demonstration of compiler theory and a practical, scalable test case generation engine.

To achieve this, the project features a **dual-engine architecture** orchestrated by an **Agentic AI Router**.

## System Architecture

### 1. Agentic AI Router (`agent_app.py`)
- **Role:** Main entry point.
- **How it works:** Uses Llama 3.2 to classify the user's natural language requirement and intelligently routes it to the most suitable engine based on complexity, required data structures, and domain constraints.
- **URL:** `http://localhost:5001`

### 2. Engine 1: Traditional Compiler Pipeline (Shiv Teja module - `shivteja.py`)
- **Focus:** Demonstrating explicit compiler theory concepts and deterministic logic.
- **Tech Stack:** Streamlit, spaCy NLP, CodeCarbon.
- **Workflow:** Strictly executes manual compiler stages:
  1. Lexical Analysis (Tokenization & Spell checking)
  2. Syntax Analysis (Grammar verification)
  3. Semantic Analysis (Constraint validation)
  4. IR Generation (Intermediate Representation)
  5. Code Generation (Test case templating)
- **Best for:** Foundational data structures (Arrays, Linked Lists, Stacks, Queues), basic authentication validation, and clear visualization of NLP parsing rules.
- **URL:** `http://localhost:8501`

### 3. Engine 2: Modern Tool-Assisted Implementation (Sameer module - `app.py`)
- **Focus:** Advanced boundary value analysis, mathematical constraint solving, and real-world scale execution.
- **Tech Stack:** Flask, Llama 3.2 (via Ollama), Z3 Theorem Prover.
- **Workflow:** 
  1. LLM intelligently parses complex constraints.
  2. Mathematical Z3 Solver validates semantics and generates precise boundary values.
  3. Security engine injects 80+ varied attack payloads.
  4. Test runner executes cases against target `.py` programs.
- **Best for:** Complex numerical bounds, exhaustive security vector testing, and live execution validation (Pass/Fail).
- **URL:** `http://localhost:5000`

## Key Features

* **Green Computing & Emissions Tracking:** Both engines track Carbon (CO2) emissions, execution time analysis, and energy consumption metrics (via CodeCarbon and custom algorithmic estimations) to promote green software engineering practices.
* **Security Risk Detection:** Capable of identifying risks spanning from targeted SQL Injection and Unauthorized Access to comprehensive automated fuzzing inputs.
* **Automated Code Execution:** (Engine 2) Ability to run the generated inputs against real Python scripts (`examples/example_programs.py`) to validate results automatically.

## Installation and Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/samdha1/NLP-Driven-Test-Case-Generator.git
   cd NLP-Driven-Test-Case-Generator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Ollama:**
   Ensure you have [Ollama](https://ollama.com/) running in the background with the `llama3.2` model installed:
   ```bash
   ollama run llama3.2
   ```

4. **Start the network of applications:**
   Open separate terminal windows and run the following commands:
   
   Starting Engine 2 (Flask API):
   ```bash
   cd NLP-Driven-Test-Case-Generator
   python app.py
   ```
   
   Starting Engine 1 (Streamlit):
   ```bash
   python -m streamlit run shivteja.py
   ```

   Starting the Agent Router (Flask API):
   ```bash
   python agent_app.py
   ```

5. **Access the application:**
   Navigate to **http://localhost:5001** in your web browser. Type your testing requirement to see the Agentic AI parse and route you to the appropriate compilation engine!
