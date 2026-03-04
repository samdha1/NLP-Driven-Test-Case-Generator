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

The project is divided into several modular components:
* Parser (spec_parser.py): Converts natural language into structured JSON objects containing min/max values and data types.
* Generator (test_generator.py): Uses the structured data to build prompts for the LLM to generate diverse test cases.
* LLM Interface (generate.py): Manages model loading, 4-bit quantization, and text generation.
* Runner (runner.py): A utility to execute the generated test cases against target Python programs to validate behavior.

## Installation and Usage

1. Clone the repository:
   git clone https://github.com/samdha1/NLP-Driven-Test-Case-Generator.git

2. Run the tool:
   You can start the generator in interactive mode by running the start script:
   python start.py

3. Commands:
   * Type your requirement (e.g., "Age must be between 18 and 60").
   * Use keywords like boundary, security, or edge to switch the focus of the test generation.
   * Type quit or exit to end the session.
