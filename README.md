# NLP-Driven Test Case Generator

The NLP-Driven Test Case Generator is an automated tool designed to bridge the gap between Natural Language (NL) software requirements and rigorous testing.It uses a combination of traditional parsing for boundary value analysis and Large Language Models (LLMs) to identify high-risk security vulnerabilities.

## Features

* Requirement Parsing: Automatically extracts data types (integer, string, boolean, float) and numerical constraints from natural language text using an LLM-based parser.
* Boundary Value Analysis: Generates test cases for exact bounds and "off-by-one" values.
* LLM Security Audits: Utilizes Llama-3.2-3B to identify risks such as SQL Injection, Buffer Overflows, and cross-site scripting (XSS).
* Multi-Input Support: Capable of detecting and parsing multiple separate requirements from a single string.
* Hardware Optimization: Configured to run efficiently on consumer-grade hardware (6GB VRAM) using 4-bit quantization.

## Technical Specifications

### Boundary Logic
The generator calculates boundary conditions based on the parsed range [min, max].For any given requirement, it generates a set of test values:
* V = {min - 1, min, min + 1, max - 1, max, max + 1}.

### LLM Implementation & Quantization
To fit the Llama-3.2-3B-Instruct model into 6GB of VRAM, the system utilizes 4-bit NormalFloat (NF4) quantization via the bitsandbytes library.This compresses model weights while maintaining the performance necessary for high-quality test generation.

### Dependencies
The project is built with Python (>=3.10) and requires the following core libraries[cite: 4]:
* torch (>=2.0.0)
* transformers (>=4.30.0)
* numpy (>=1.24.0)

## System Architecture

The pipeline follows the proposed architecture from user input to verified results:

1. **User** → Natural language requirement.
2. **Phase 3: NLP Layer** (`start.py` → `complex/complex_spec.py`):
   * Natural language is parsed (with LLM inference) into a **Structured JSON Spec** (min, max, data_type, constraints).
3. **Phase 4 & 5: Hybrid Logic Layer**:
   * **Numerical constraints** from the spec → **Z3 Solver Engine** (`solver/z3_engine.py`) → precise logic values (boundaries, constraint-satisfying values).
   * **Security context** from the spec → **LLM Security Engine** (`security/llm_security_engine.py`) → creative security strings (SQLi, XSS, overflow, etc.).
   * **Test Case Aggregator** (`aggregator/aggregator.py`) merges both streams into a single list of test cases.
4. **Execution**: **runner.py** runs each test case against a target program (e.g. `examples/example_programs.py`).
5. **Verified results** are reported back to the user (pass/fail, output, errors).

### Components

| Component | Role |
|-----------|------|
| **complex/complex_spec.py** | NLP → structured JSON spec (LLM + regex fallback). |
| **z3_engine.py** | Numerical constraints → boundary and constraint-satisfying values (Z3 when available). |
| **llm_security_engine.py** | Security context → creative security test inputs (LLM or fallback payloads). |
| **aggregator.py** | Combines Z3 and LLM outputs into unified test cases. |
| **** | Legacy LLM-based generator (boundary/security/edge prompts). |
| **generate.py** | LLM loading and text generation. |
| **runner.py** | Executes test cases against a target script and returns results. |

## Installation and Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/samdha1/NLP-Driven-Test-Case-Generator.git
   cd NLP-Driven-Test-Case-Generator
   pip install -r requirements.txt
   ```

2. **CLI / interactive mode:**
   ```bash
   python start.py
   ```
   * Type your requirement (e.g., "Age must be between 18 and 60").
   * Use keywords like boundary, security, or edge to switch the focus of the test generation.
   * Type quit or exit to end the session.

3. **Web frontend (HTML/CSS):**
   ```bash
   python app.py
   ```
   Then open **http://localhost:5000** in your browser.
   * Enter a requirement or a LeetCode/Codeforces-style problem statement.
   * Click **Generate** to see the **Structured JSON Spec** and **Test Cases**.
   * Click **Generate** to see the **Structured JSON Spec** and **Test Cases** (and, when complex mode is on, **Complex Spec** and **Complex Test Cases** with formatted multi-line output).
