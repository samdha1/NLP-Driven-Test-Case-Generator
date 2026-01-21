# NLP-Driven Test Case Generator

 NLP-Driven Test Case Generator is an automated tool designed to bridge the gap between Natural Language (NL) software requirements and rigorous testing. It uses traditional parsing for boundary value analysis and leverages Large Language Models (LLMs)—specifically **Llama-3.2-3B**—to identify high-risk security vulnerabilities.

## 🚀 Features

* **Requirement Parsing**: Automatically extracts data types (integer, string, boolean, float) and numerical constraints from natural language text.
* **Boundary Value Analysis**: Generates test cases for exact bounds and "off-by-one" values.
* **LLM Security Audits**: Utilizes Llama-3.2-3B to identify risks such as Buffer Overflows and SQL Injection.
* **GPU Optimization**: Configured to run efficiently on 6GB VRAM hardware using 4-bit quantization.

## 🧮 Technical Specifications

### Boundary Logic
The generator calculates boundary conditions based on the parsed range $[min, max]$. For any given requirement, it generates the set of test values $V$:

V = \{min - 1, min, max, max + 1\}


### 4-Bit Quantization (NF4)
To fit the model into 6GB of VRAM, we use **4-bit NormalFloat (NF4)** quantization. The weights are compressed using:
Quantized Weight = round( Weight / Scale ) 
This allows the **Llama-3.2-3B** model to run on consumer-grade GPUs like the RTX 3050.

### Memory Monitoring
We track GPU VRAM allocation in GiB using the conversion:
 GiB = bytes/1024^3

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/samdha1/NLP-Driven-Test-Case-Generator.git
