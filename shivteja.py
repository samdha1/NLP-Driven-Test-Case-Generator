import time
import pandas as pd
from codecarbon import EmissionsTracker
import psutil

import random
import string
import spacy
nlp = spacy.load("en_core_web_sm")
from spellchecker import SpellChecker
spell = SpellChecker()

def detect_security_risk(requirement):

    req = requirement.lower()
    risks = []

    if "login" in req or "database" in req:
        risks.append("SQL Injection Risk")

    if "script" in req or "html" in req:
        risks.append("Cross-Site Scripting (XSS) Risk")

    if "admin" in req or "access" in req:
        risks.append("Unauthorized Access Risk")

    if "upload" in req or "file" in req:
        risks.append("File Upload Attack Risk")

    if "modify" in req or "change code" in req:
        risks.append("Code Tampering Risk")

    return risks
def generate_valid_password():
    upper = random.choice(string.ascii_uppercase)
    lower = random.choice(string.ascii_lowercase)
    digits = random.choice(string.digits)
    special = random.choice(string.punctuation)
    remaining = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=4))
    password = upper + lower + digits + special + remaining
    return ''.join(random.sample(password,len(password)))

def generate_invalid_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k = 8))

def generate_short_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k = 3))
def generate_long_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k = 100))

def lexical_analyzer(requirement):

    requirement = requirement.lower()
    requirement = requirement.replace("linked list", "linked_list")
    words = requirement.lower().split()

    technical_words = {
        "stack", "queue", "array", "linked_list", "tree", "graph", "heap",
        "push", "pop", "enqueue", "dequeue", "insert", "delete", "remove",
        "max", "min", "sum", "reverse", "sort", "size", "length","security","login","password","attack",
        "admin","upload","file","script",
        "database","malicious"
    }
    filtered_words = [w for w in words if w not in technical_words]

    misspelled = spell.unknown(filtered_words)

    if misspelled:
        errors = []
        for word in misspelled:
            suggestion = spell.correction(word)
            errors.append(f"LEXICAL ERROR : Unknown token '{word}' -> Did you mean '{suggestion}'?")
        return "\n".join(errors)

    doc = nlp(requirement)

    structure = {
        "CONDITION": None,
        "ACTOR": None,
        "ACTION": None,
        "OBJECT": None,
        "ATTRIBUTE": None,
        "OUTCOME": None
    }

    data_structures = [
        "array", "list", "stack", "queue",
        "linked_list", "tree", "graph", "heap"
    ]

    for token in doc:
        if token.pos_ == "VERB":
            structure["ACTION"] = token.lemma_.lower()
            break

    if structure["ACTION"] is None and len(doc) > 0:
        structure["ACTION"] = doc[0].lemma_.lower()

    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"]:
            structure["OBJECT"] = token.lemma_.lower()
            break

    for token in doc:
        if token.text.lower() in ["valid", "invalid", "empty"]:
            structure["ATTRIBUTE"] = token.text.lower()

    for token in doc:
        if token.text.lower() in ["success", "failure", "error"]:
            structure["OUTCOME"] = token.text.lower()

    for token in doc:
        if token.text.lower() in ["if", "when", "unless"]:
            structure["CONDITION"] = token.text.lower()

    for token in doc:
        if token.dep_ == "nsubj":
            structure["ACTOR"] = token.lemma_.lower()
            break

    if structure["ACTOR"] is None:
        structure["ACTOR"] = "system"

    req_lower = requirement.lower()

    for ds in data_structures:
        if ds in req_lower:
            structure["OBJECT"] = ds
            break

    stop_words = {"in", "the", "a", "an", "into", "of", "to"}
    tokens = [word for word in words if word not in stop_words]

    if structure["OBJECT"] == "linked_list":
        structure["OBJECT"] = "linked list"

    return {
        "tokens": tokens,
        "structure": structure
    }

def syntax_analyzer(structure, requirement):

    if structure["ACTION"] is None:
        return "SYNTAX ERROR: No action (verb) found in requirement"

    if structure["OBJECT"] is None:
        return "SYNTAX ERROR: No object found in requirement"

    sentence_pattern = []

    if structure["ACTOR"]:
        sentence_pattern.append("ACTOR")

    sentence_pattern.append("ACTION")

    if structure["OBJECT"]:
        sentence_pattern.append("OBJECT")

    if structure["ATTRIBUTE"]:
        sentence_pattern.append("ATTRIBUTE")

    if structure["OUTCOME"]:
        sentence_pattern.append("OUTCOME")

    pattern = " -> ".join(sentence_pattern)

    result = {
        "Sentence Pattern": pattern,
        "Grammar Rule": "[ACTOR] -> [ACTION] -> [OBJECT]",
        "Syntax Status": "Valid Requirement Sentence"
    }

    req_lower = requirement.lower()

    algorithm_actions = ["sum", "find", "calculate", "return", "max", "min", "reverse", "sort", "add", "insert"]

    if structure["ACTION"] in algorithm_actions:
        if not any(ds in req_lower for ds in ["array", "stack", "queue", "list", "linked list"]):
            return "SYNTAX ERROR: Data structure not specified for algorithm action"

    return result

def semantic_analyzer(structure):

    if type(structure) == str:
        return "Semantic Skipped (Syntax Error)"

    attribute = structure["ATTRIBUTE"]
    outcome = structure["OUTCOME"]

    if attribute == "invalid" and outcome == "success":
        return "Semantic Error : Invalid input cannot lead to success"

    array_operations = ["max", "min", "reverse", "sort", "sum", "size", "length"]
    stack_operations = ["push", "pop"]
    queue_operations = ["enqueue", "dequeue"]

    obj = structure["OBJECT"]
    action = structure["ACTION"]

    if structure["ATTRIBUTE"] == "empty":

        if obj in ["array", "list"] and action in ["sort", "reverse", "max", "min"]:
            return f"Semantic Error : Cannot perform '{action}' on an empty {obj}"

        if obj == "stack" and action == "pop":
            return "Semantic Error : Cannot pop from an empty stack"

        if obj == "queue" and action == "dequeue":
            return "Semantic Error : Cannot dequeue from an empty queue"

    if action in array_operations and obj not in ["array", "list"]:
        return f"Semantic Error : '{action}' operation requires an array or list"

    if action in stack_operations and obj != "stack":
        return f"Semantic Error : '{action}' operation requires a stack"

    if action in queue_operations and obj != "queue":
        return f"Semantic Error : '{action}' operation requires a queue"

    return "Semantic Analysis Passed"

def ir_generator(structure):

    if type(structure) == str:
        return None

    ir = {
        "actor": structure["ACTOR"],
        "action": structure["ACTION"],
        "object": structure["OBJECT"],
        "input_type": structure["ATTRIBUTE"],
        "condition": structure["CONDITION"],
        "expected_result": structure["OUTCOME"]
    }

    return ir

def generate_test_cases(ir,requirement):

    test_cases = []
    req_lower = requirement.lower()

    if "max" in req_lower and "array" in req_lower:
        arr = [random.randint(0,50) for _ in range(random.randint(3,6))]
        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": f"{arr}",
            "Expected Output": f"{max(arr)}"
        })
        arr = [random.randint(-50, -1) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": f"{arr}",
            "Expected Output": f"{max(arr)}"
        })
        arr = [random.randint(-50,50) for _ in range(random.randint(3,6))]
        test_cases.append({
            "Test Case ID": "TC_03",
            "Input": f"{arr}",
            "Expected Output": f"{max(arr)}"
        })
        single = [random.randint(-50,50)]
        test_cases.append({
            "Test Case ID": "TC_04",
            "Input": f"{single}",
            "Expected Output": f"{single[0]}"
        })
        test_cases.append({
            "Test Case ID": "TC_05",
            "Input": "Empty Array []",
            "Expected Output": "Error: No elements in array"
        })

    elif "min" in req_lower and "array" in req_lower:
        arr = [random.randint(0, 50) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": f"{arr}",
            "Expected Output": f"{min(arr)}"
        })
        arr = [random.randint(-50, -1) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": f"{arr}",
            "Expected Output": f"{min(arr)}"
        })
        arr = [random.randint(-50,50) for _ in range(random.randint(3,6))]
        test_cases.append({
            "Test Case ID": "TC_03",
            "Input": f"{arr}",
            "Expected Output": f"{min(arr)}"
        })
        single = [random.randint(-50,50)]
        test_cases.append({
            "Test Case ID": "TC_04",
            "Input": f"{single}",
            "Expected Output": f"{single[0]}"
        })
        test_cases.append({
            "Test Case ID": "TC_05",
            "Input": "Empty Array []",
            "Expected Output": "Error: No elements in array"
        })

    elif "sum" in req_lower and "array" in req_lower:
        arr = [random.randint(0, 50) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": f"{arr}",
            "Expected Output": f"{sum(arr)}"
        })
        arr = [random.randint(-50, -1) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": f"{arr}",
            "Expected Output": f"{sum(arr)}"
        })
        arr = [random.randint(-50,50) for _ in range(random.randint(3,6))]
        test_cases.append({
            "Test Case ID": "TC_03",
            "Input": f"{arr}",
            "Expected Output": f"{sum(arr)}"
        })
        single = [random.randint(-50, 50)]
        test_cases.append({
            "Test Case ID": "TC_04",
            "Input": f"{single}",
            "Expected Output": f"{sum(single)}"
        })
        test_cases.append({
            "Test Case ID": "TC_05",
            "Input": "[]",
            "Expected Output": "0"
        })

    elif "reverse" in req_lower and "array" in req_lower:
        arr = [random.randint(0, 50) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": f"{arr}",
            "Expected Output": f"{arr[::-1]}"
        })
        arr = [random.randint(-50, -1) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": f"{arr}",
            "Expected Output": f"{arr[::-1]}"
        })
        arr = [random.randint(-50,50) for _ in range(random.randint(3,6))]
        test_cases.append({
            "Test Case ID": "TC_03",
            "Input": f"{arr}",
            "Expected Output": f"{arr[::-1]}"
        })
        single = [random.randint(-50, 50)]
        test_cases.append({
            "Test Case ID": "TC_04",
            "Input": f"{single}",
            "Expected Output": f"{single[::-1]}"
        })
        test_cases.append({
            "Test Case ID": "TC_05",
            "Input": "[]",
            "Expected Output": "Error : No element in array"
        })

    elif ("size" in req_lower or "length" in req_lower) and "array" in req_lower:
        arr = [random.randint(0, 50) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": f"{arr}",
            "Expected Output": f"{len(arr)}"
        })
        arr = [random.randint(-50, 50) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": f"{arr}",
            "Expected Output": f"{len(arr)}"
        })
        arr = [random.randint(-50,50) for _ in range(random.randint(10,16))]
        test_cases.append({
            "Test Case ID": "TC_03",
            "Input": f"{arr}",
            "Expected Output": f"{len(arr)}"
        })
        single = [random.randint(-50, 50)]
        test_cases.append({
            "Test Case ID": "TC_04",
            "Input": f"{single}",
            "Expected Output": f"{len(single)}"
        })
        test_cases.append({
            "Test Case ID": "TC_05",
            "Input": "[]",
            "Expected Output": "Error : No element in array"
        })

    elif "sort" in req_lower and "array" in req_lower:

        arr = [random.randint(0, 50) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": f"{arr}",
            "Expected Output": f"{sorted(arr)}"
        })
        arr = [random.randint(-50, 0) for _ in range(random.randint(3, 6))]
        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": f"{arr}",
            "Expected Output": f"{sorted(arr)}"
        })
        arr = [random.randint(-50,50) for _ in range(random.randint(10,16))]
        test_cases.append({
            "Test Case ID": "TC_03",
            "Input": f"{arr}",
            "Expected Output": f"{sorted(arr)}"
        })
        single = [random.randint(-50, 50)]
        test_cases.append({
            "Test Case ID": "TC_04",
            "Input": f"{single}",
            "Expected Output": f"{sorted(single)}"
        })
        test_cases.append({
            "Test Case ID": "TC_05",
            "Input": "[]",
            "Expected Output": "Error : No element in array"
        })


    elif "linked list" in req_lower and "insert" in req_lower:

        ll = [random.randint(-50, 50) for _ in range(random.randint(3, 6))]

        def format_linked_list(lst):

            if not lst:
                return "NULL"

            return " -> ".join(map(str, lst)) + " -> NULL"

        value = random.randint(1, 50)
        new_list = ll.copy()
        new_list.insert(0, value)
        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": f"List = {format_linked_list(ll)}, Insert {value} at head",
            "Expected Output": format_linked_list(new_list)
        })

        new_list = ll.copy()
        new_list.append(value)
        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": f"List = {format_linked_list(ll)}, Insert {value} at tail",
            "Expected Output": format_linked_list(new_list)
        })

        pos = random.randint(1, len(ll) - 1)
        new_list = ll.copy()
        new_list.insert(pos, value)
        test_cases.append({
            "Test Case ID": "TC_03",
            "Input": f"List = {format_linked_list(ll)}, Insert {value} at position {pos}",
            "Expected Output": format_linked_list(new_list)
        })

        empty = []
        new_list = [value]
        test_cases.append({
            "Test Case ID": "TC_04",
            "Input": f"List = NULL, Insert {value}",
            "Expected Output": format_linked_list(new_list)
        })

        invalid_pos = len(ll) + 5
        test_cases.append({
            "Test Case ID": "TC_05",
            "Input": f"List = {format_linked_list(ll)}, Insert {value} at position {invalid_pos}",
            "Expected Output": "Error: Position out of bounds"
        })

    elif "linked list" in req_lower and ("remove" in req_lower or "delete" in req_lower):
        ll = [random.randint(1, 50) for _ in range(5)]
        def format_linked_list(lst):
            return " -> ".join(map(str, lst)) + " -> NULL"
        pos = random.randint(0, len(ll) - 1)
        new_list = ll.copy()
        deleted = new_list.pop(pos)

        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": f"{format_linked_list(ll)}, Delete node at position {pos}",
            "Expected Output": format_linked_list(new_list)
        })

        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": "Delete from empty list",
            "Expected Output": "Error: List Empty"
        })

    elif "stack" in req_lower and  "push" in req_lower :

        stack = []

        def format_stack_tube(stack):

            if not stack:
                return "Stack is Empty"

            width = 7
            output = "        Top\n"
            output += "   ┌" + "─" * width + "┐\n"

            for element in reversed(stack):
                output += f"   │ {str(element).center(width - 2)} │\n"

            output += "   └" + "─" * width + "┘\n"

            return output

        for i in range(1, 6):
            value = random.randint(1, 50)
            stack.append(value)

            test_cases.append({
                "Test Case ID": f"TC_0{i}",
                "Input": f"Push {value} into stack",
                "Expected Output": format_stack_tube(stack.copy())
            })
        test_cases.append({
            "Test Case ID": "TC_06",
            "Input": "Push element into full stack",
            "Expected Output": "Stack Overflow"
        })

    elif "stack" in req_lower and "pop" in req_lower:

        stack = []

        def format_stack_tube(stack):

            if not stack:
                return "Stack is Empty"

            width = 7

            output = "        Top\n"

            output += "   ┌" + "─" * width + "┐\n"

            for element in reversed(stack):
                output += f"   │ {str(element).center(width - 2)} │\n"

            output += "   └" + "─" * width + "┘\n"

            return output

        for i in range(5):
            stack.append(random.randint(1, 50))
        test_cases.append({
            "Test Case ID": "TC_00",
            "Input": "Initial Stack",
            "Expected Output": format_stack_tube(stack.copy())
        })
        for i in range(1, 6):
            popped = stack.pop()
            test_cases.append({
                "Test Case ID": f"TC_0{i}",
                "Input": "Pop element from stack",
                "Expected Output":
                 f"Popped Element: {popped}\n\n"
                 f"Stack After Pop:\n{format_stack_tube(stack.copy())}"
            })
        test_cases.append({
            "Test Case ID": "TC_06",
            "Input": "Pop element from empty stack",
            "Expected Output": "Stack Underflow"
        })

    elif "queue" in req_lower and ("enqueue" in req_lower or "add" in req_lower):

        queue = []

        def format_queue(queue):

            if not queue:
                return "Queue is Empty"

            width = 7
            output = "Front → "

            for element in queue:
                output += f"[ {element} ] "

            output += "← Rear"

            return output

        for i in range(1, 6):
            value = random.randint(1, 50)
            queue.append(value)

            test_cases.append({
                "Test Case ID": f"TC_0{i}",
                "Input": f"Enqueue {value} into queue",
                "Expected Output": format_queue(queue.copy())
            })

        test_cases.append({
            "Test Case ID": "TC_06",
            "Input": "Enqueue element into full queue",
            "Expected Output": "Queue Overflow"
        })

    elif "queue" in req_lower and "dequeue" in req_lower:

        queue = []

        def format_queue(queue):

            if not queue:
                return "Queue is Empty"

            output = "Front → "

            for element in queue:
                output += f"[ {element} ] "

            output += "← Rear"

            return output

        for i in range(5):
            queue.append(random.randint(1, 50))

        test_cases.append({
            "Test Case ID": "TC_00",
            "Input": "Initial Queue",
            "Expected Output": format_queue(queue.copy())
        })

        for i in range(1, 6):
            removed = queue.pop(0)

            test_cases.append({
                "Test Case ID": f"TC_0{i}",
                "Input": "Dequeue element from queue",
                "Expected Output":
                    f"Removed Element: {removed}\n\n"
                    f"Queue After Dequeue:\n{format_queue(queue.copy())}"
            })

        test_cases.append({
            "Test Case ID": "TC_06",
            "Input": "Dequeue element from empty queue",
            "Expected Output": "Queue Underflow"
        })

    elif "password" in req_lower:

        valid_pass = generate_valid_password()
        invalid_pass = generate_invalid_password()
        short_pass = generate_short_password()
        long_pass = generate_long_password()

        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": valid_pass,
            "Expected Output": "Password Accepted"
        })
        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": ''.join(random.choices(string.ascii_lowercase + string.digits, k = 8)),
            "Expected Output": "Password must contain uppercase and special characters"
        })
        test_cases.append({
            "Test Case ID": "TC_03",
            "Input": short_pass,
            "Expected Output": "Password too short"
        })
        test_cases.append({
            "Test Case ID": "TC_04",
            "Input": long_pass,
            "Expected Output": "Password too long"
        })
        test_cases.append({
            "Test Case ID": "TC_05",
            "Input": " ",
            "Expected Output": "Password Required"
        })

    elif "login" in req_lower:
        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": "Username ' '",
            "Expected Output": "Username Required"
        })
        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": "Password ' '",
            "Expected Output": "Password Required"
        })
        test_cases.append({
            "Test Case ID": "TC_03",
            "Input": "Username ' ' Password ' '",
            "Expected Output": "Credentials Required"
        })
        test_cases.append({
            "Test Case ID": "TC_04",
            "Input": "5 Wrong Passwords ",
            "Expected Output": "Account Blocked"
        })
        test_cases.append({
            "Test Case ID": "TC_05",
            "Input": "Correct Password After Lock ",
            "Expected Output": "Access Denied"
        })
        test_cases.append({
            "Test Case ID": "TC_06",
            "Input": "Correct Password Before Limit ",
            "Expected Output": "Login Success "
        })


    elif "upload" in req_lower and "file" in req_lower:

        valid_extensions = ["pdf", "png", "jpg", "jpeg"]
        dangerous_extensions = ["exe", "php", "bat"]
        valid_file = "file" + str(random.randint(1, 100)) + "." + random.choice(valid_extensions)

        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": valid_file,
            "Expected Output": "Upload Success"
        })

        dangerous_file = "file" + str(random.randint(1, 100)) + "." + random.choice(dangerous_extensions)

        test_cases.append({
            "Test Case ID": "TC_02",
            "Input": dangerous_file,
            "Expected Output": "Invalid file type"
        })
        test_cases.append({
            "Test Case ID": "TC_03",
            "Input": " ",
            "Expected Output": "No file selected"
        })

        large_file = "large_file_" + str(random.randint(100, 500)) + "MB.zip"
        test_cases.append({
            "Test Case ID": "TC_04",
            "Input": large_file,
            "Expected Output": "File size exceeds limit"
        })
        test_cases.append({
            "Test Case ID": "TC_05",
            "Input": "image.jpg.exe",
            "Expected Output": "Suspicious file detected"
        })

    if not test_cases:
        test_cases.append({
            "Test Case ID": "TC_01",
            "Input": "Unsupported Requirement",
            "Expected Output": "No test case template available"
        })

    return test_cases

import streamlit as st

st.title("NLP Test Case Generator")

default_req = ""
try:
    if hasattr(st, "query_params") and "requirement" in st.query_params:
        default_req = st.query_params["requirement"]
    elif hasattr(st, "experimental_get_query_params"):
        params = st.experimental_get_query_params()
        if "requirement" in params:
            default_req = params["requirement"][0]
except Exception:
    pass

requirement = st.text_input("Enter Requirement", value=default_req)

if st.button("Generate Test Cases"):

    risks = detect_security_risk(requirement)

    if risks:
        st.subheader("Security Risk Detection")

        security_test_cases = []

        for r in risks:
            st.warning(f"⚠ {r}")

            if r == "SQL Injection Risk":
                security_test_cases.append({
                    "Test Case ID": "SEC_TC_01",
                    "Input": "username=' OR '1'='1",
                    "Expected Output": "Login rejected"
                })

            if r == "Unauthorized Access Risk":
                security_test_cases.append({
                    "Test Case ID": "SEC_TC_02",
                    "Input": "Guest accessing admin panel",
                    "Expected Output": "Access Denied"
                })

            if r == "File Upload Attack Risk":
                security_test_cases.append({
                    "Test Case ID": "SEC_TC_03",
                    "Input": "Upload .exe file",
                    "Expected Output": "File rejected"
                })

        st.subheader("Security Test Cases")
        st.table(pd.DataFrame(security_test_cases))

    tracker = EmissionsTracker()
    tracker.start()

    cpu_start = psutil.cpu_percent(interval = None)
    memory_start = psutil.virtual_memory().percent

    start = time.perf_counter()
    lex_result = lexical_analyzer(requirement)
    lex_time = time.perf_counter() - start

    st.subheader("Lexical Analysis")
    if isinstance(lex_result, str):
        st.error(lex_result)
        st.error("Compilation stopped due to Lexical Error")
        st.stop()

    st.write("**Tokens:**")
    st.code(lex_result["tokens"])

    structure = lex_result["structure"]

    st.write("**Lexical Structure:**")
    st.json(structure)

    start = time.perf_counter()
    syntax_result = syntax_analyzer(structure, requirement)
    syntax_time = time.perf_counter() - start

    st.subheader("Syntax Analysis")

    if isinstance(syntax_result, dict):
        for key, value in syntax_result.items():
            st.write(f"**{key}:** {value}")
    else:
        st.error(syntax_result)

    if isinstance(syntax_result, str) and "SYNTAX ERROR" in syntax_result:
        st.error("Compilation stopped due to Syntax Error")
        st.stop()

    start = time.perf_counter()
    semantic_result = semantic_analyzer(structure)
    semantic_time = time.perf_counter() - start

    st.subheader("Semantic Analysis")
    st.write(semantic_result)

    if "Semantic Error" in semantic_result:
        st.error("Compilation stopped due to Semantic Error")
        st.stop()

    start = time.perf_counter()
    ir = ir_generator(structure)
    ir_time = time.perf_counter() - start

    st.subheader("Intermediate Representation")
    ir_display = {k: (v if v else "None") for k, v in ir.items()}
    st.table(pd.DataFrame(ir_display.items(), columns=["Field", "Value"]))

    start = time.perf_counter()
    test_cases = generate_test_cases(ir, requirement)
    test_cases_time = time.perf_counter() - start

    st.subheader("Generated Test Cases")

    for i, tc in enumerate(test_cases, 1):
        st.write(f"### Test Case {i}")

        for key, value in tc.items():
            if key == "Expected Output":
                st.write(f"**{key}:**")
                st.code(value)
            else:
                st.write(f"**{key}:** {value}")

    emissions = tracker.stop()

    cpu_end = psutil.cpu_percent(interval = None)
    memory_end = psutil.virtual_memory().percent

    st.subheader("Green Compiler Metrics")
    st.subheader("Carbon Emission Indicator")
    st.write("Carbon Emissions ( in kg CO2 ) : ", emissions)
    if emissions < 0.001:
        st.success("🟢 Very Low Carbon Emission")
    elif emissions < 0.01:
        st.warning("🟡 Moderate Carbon Emission")
    else:
        st.error("🔴 High Carbon Emission")

    energy = (cpu_end - cpu_start) * 0.001
    st.write("Estimated Energy Consumption (KWh) : ", energy)

    data = {
        "Stage": ["Lexical", "Syntax", "Semantic", "IR", "Test Case"],
        "Execution Time": [lex_time * 1000,
                           syntax_time * 1000,
                           semantic_time * 1000,
                           ir_time * 1000,
                           test_cases_time * 1000
                           ],
    }

    df = pd.DataFrame(data)
    st.subheader("Execution Time Analysis (milliseconds)")
    st.bar_chart(df.set_index("Stage"))