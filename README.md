\documentclass[12pt]{article}
\usepackage[a4paper,margin=1in]{geometry}
\usepackage{hyperref}
\usepackage{listings}
\usepackage{xcolor}

\lstset{
    basicstyle=\ttfamily\small,
    breaklines=true,
    frame=single,
    backgroundcolor=\color{gray!10},
    keywordstyle=\color{blue},
    commentstyle=\color{green!60!black},
    stringstyle=\color{red},
}

\title{\textbf{NLP-Driven Test Case Generator}}
\author{}
\date{}

\begin{document}

\maketitle

\section{Introduction}
\textbf{NLP-Driven Test Case Generator} is an automated tool designed to bridge the gap between Natural Language (NL) software requirements and rigorous testing. It uses traditional parsing for boundary value analysis and leverages Large Language Models (LLMs)---specifically \textbf{Llama-3.2-3B}---to identify high-risk security vulnerabilities.

\section{Features}
\begin{itemize}
    \item \textbf{Requirement Parsing}: Automatically extracts data types (integer, string, boolean, float) and numerical constraints from natural language text.
    \item \textbf{Boundary Value Analysis}: Generates test cases for exact bounds, as well as ``off-by-one'' values (just above and just below limits).
    \item \textbf{LLM Security Audits}: Utilizes Llama-3.2-3B to identify risks such as Buffer Overflows, SQL Injection, and Integer Overflows based on software requirements.
    \item \textbf{GPU Optimization}: Configured to run efficiently on 6GB VRAM hardware (like the RTX 3050) using 4-bit quantization.
    \item \textbf{Automated Runner}: Includes a module to execute generated tests against target applications and capture success, failure, or system crashes.
\end{itemize}

\section{Installation}
Ensure you have Python 3.10 or higher installed.

\subsection{Clone the repository}
\begin{lstlisting}[language=bash]
git clone https://github.com/samdha1/NLP-Driven-Test-Case-Generator.git
\end{lstlisting}

\subsection{Install the package and dependencies}
\begin{lstlisting}[language=bash]
pip install .
\end{lstlisting}

Dependencies include: torch, transformers, numpy, spacy, and tokenizers.

\section{Usage}

\subsection{Automated Security Audit}
Run the specialized security script to analyze a requirement using Llama-3.2:
\begin{lstlisting}[language=bash]
python llama_security_test.py
\end{lstlisting}

\subsection{CLI Boundary Generation}
Generate standard boundary test cases directly from the command line:
\begin{lstlisting}[language=bash]
nlp_testgen --spec "The application accepts a user_id string between 5 and 10 characters."
\end{lstlisting}

\subsection{AI Risk Analysis}
Generate general security risks for web inputs using the built-in AI module:
\begin{lstlisting}[language=bash]
python test_ai.py
\end{lstlisting}

\section{Project Structure}
\begin{itemize}
    \item \texttt{src/nlp\_testgen/parser/}: Extracts constraints and types from NL.
    \item \texttt{src/nlp\_testgen/generator/}: Logic for calculating boundary test values.
    \item \texttt{src/nlp\_testgen/llm/}: Model loading, quantization, and text generation logic.
    \item \texttt{src/nlp\_testgen/runner/}: Executes tests and monitors for program crashes.
    \item \texttt{examples/}: Sample programs to test the generator against.
\end{itemize}

\section{License}
Refer to the \texttt{LICENSE} file in the root directory for details.

\end{document}
