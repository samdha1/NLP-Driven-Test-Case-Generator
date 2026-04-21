import time
import secrets
import re
import pandas as pd
from codecarbon import EmissionsTracker
import psutil

import random
import string
import spacy
nlp = spacy.load("en_core_web_sm")
from spellchecker import SpellChecker
spell = SpellChecker()

psutil.cpu_percent(interval=0.1)


def ok(data):
    """Wrap a successful analysis result."""
    return {"ok": True, "data": data}

def err(message):
    """Wrap a failed analysis result."""
    return {"ok": False, "error": message}

def is_ok(result):
    return isinstance(result, dict) and result.get("ok") is True

def is_err(result):
    return isinstance(result, dict) and result.get("ok") is False



def detect_security_risk(requirement):
    req = requirement.lower()
    risks = []

    if re.search(r'\blogin\b', req) or re.search(r'\bdatabase\b', req):
        risks.append("SQL Injection Risk")

    if re.search(r'<script|javascript:|html\s+script|\bxss\b', req):
        risks.append("Cross-Site Scripting (XSS) Risk")

    if re.search(r'\badmin\b', req) or re.search(r'\baccess\b', req):
        risks.append("Unauthorized Access Risk")

    if re.search(r'\bupload\b', req) and re.search(r'\bfile\b', req):
        risks.append("File Upload Attack Risk")

    if re.search(r'\bmodify\b', req) or re.search(r'change\s+code', req):
        risks.append("Code Tampering Risk")

    return risks


def generate_valid_password():
    """Cryptographically-safe valid password (uppercase + lowercase + digit + special)."""
    upper   = secrets.choice(string.ascii_uppercase)
    lower   = secrets.choice(string.ascii_lowercase)
    digit   = secrets.choice(string.digits)
    special = secrets.choice(string.punctuation)
    pool    = string.ascii_letters + string.digits + string.punctuation
    rest    = ''.join(secrets.choice(pool) for _ in range(4))
    pwd     = list(upper + lower + digit + special + rest)
    random.shuffle(pwd)
    return ''.join(pwd)

def generate_invalid_password():
    """Only lowercase + digits — guaranteed to fail uppercase+special check."""
    return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))

def generate_short_password():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(3))

def generate_long_password():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(100))



def lexical_analyzer(requirement):
    if len(requirement) > 500:
        return err("LEXICAL ERROR: Input too long (max 500 characters)")

    if not requirement.strip():
        return err("LEXICAL ERROR: Empty requirement")

    requirement = requirement.lower()
    requirement = requirement.replace("linked list", "linked_list")
    words = requirement.split()

    technical_words = {
        "stack", "queue", "array", "linked_list", "tree", "graph", "heap",
        "push", "pop", "enqueue", "dequeue", "insert", "delete", "remove",
        "max", "min", "sum", "reverse", "sort", "size", "length",
        "security", "login", "password", "attack",
        "admin", "upload", "file", "script",
        "database", "malicious",
        # heap / tree / graph extras
        "binary", "node", "root", "leaf", "edge", "vertex", "vertices",
        "inorder", "preorder", "postorder", "search", "traversal",
        "heapify", "extract",
    }

    filtered_words = [w for w in words if w not in technical_words]
    misspelled = spell.unknown(filtered_words)

    if misspelled:
        errors = []
        for word in misspelled:
            suggestion = spell.correction(word)
            errors.append(
                f"LEXICAL ERROR: Unknown token '{word}' → Did you mean '{suggestion}'?"
            )
        return err("\n".join(errors))

    doc = nlp(requirement)

    structure = {
        "CONDITION": None,
        "ACTOR":     None,
        "ACTION":    None,
        "OBJECT":    None,
        "ATTRIBUTE": None,
        "OUTCOME":   None,
    }

    data_structures = [
        "array", "list", "stack", "queue",
        "linked_list", "tree", "graph", "heap",
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
    tokens = [w for w in words if w not in stop_words]

    if structure["OBJECT"] == "linked_list":
        structure["OBJECT"] = "linked list"

    fields = ["ACTOR", "ACTION", "OBJECT", "ATTRIBUTE", "OUTCOME"]
    found  = sum(1 for f in fields if structure[f] is not None)
    coverage = round((found / len(fields)) * 100)

    return ok({
        "tokens":   tokens,
        "structure": structure,
        "coverage": coverage,
    })


def syntax_analyzer(structure, requirement):
    if structure["ACTION"] is None:
        return err("SYNTAX ERROR: No action (verb) found in requirement")

    if structure["OBJECT"] is None:
        return err("SYNTAX ERROR: No object found in requirement")

    sentence_pattern = []
    if structure["ACTOR"]:    sentence_pattern.append("ACTOR")
    sentence_pattern.append("ACTION")
    if structure["OBJECT"]:   sentence_pattern.append("OBJECT")
    if structure["ATTRIBUTE"]: sentence_pattern.append("ATTRIBUTE")
    if structure["OUTCOME"]:  sentence_pattern.append("OUTCOME")

    pattern = " → ".join(sentence_pattern)

    req_lower = requirement.lower()
    algorithm_actions = [
        "sum", "find", "calculate", "return", "max", "min",
        "reverse", "sort", "add", "insert",
    ]

    if structure["ACTION"] in algorithm_actions:
        ds_terms = ["array", "stack", "queue", "list", "linked list",
                    "tree", "graph", "heap"]
        if not any(ds in req_lower for ds in ds_terms):
            return err("SYNTAX ERROR: Data structure not specified for algorithm action")

    return ok({
        "Sentence Pattern": pattern,
        "Grammar Rule":     "[ACTOR] → [ACTION] → [OBJECT]",
        "Syntax Status":    "Valid Requirement Sentence",
    })



def semantic_analyzer(structure):
    """
    `structure` here is the raw lexical structure dict (ACTOR/ACTION/…).
    The caller must only invoke this after syntax has passed.
    """
    attribute = structure["ATTRIBUTE"]
    outcome   = structure["OUTCOME"]

    if attribute == "invalid" and outcome == "success":
        return err("Semantic Error: Invalid input cannot lead to success")

    array_operations = ["max", "min", "reverse", "sort", "sum", "size", "length"]
    stack_operations = ["push", "pop"]
    queue_operations = ["enqueue", "dequeue"]

    obj    = structure["OBJECT"]
    action = structure["ACTION"]

    if structure["ATTRIBUTE"] == "empty":
        if obj in ["array", "list"] and action in ["sort", "reverse", "max", "min"]:
            return err(f"Semantic Error: Cannot perform '{action}' on an empty {obj}")
        if obj == "stack" and action == "pop":
            return err("Semantic Error: Cannot pop from an empty stack")
        if obj == "queue" and action == "dequeue":
            return err("Semantic Error: Cannot dequeue from an empty queue")

    if action in array_operations and obj not in ["array", "list"]:
        return err(f"Semantic Error: '{action}' operation requires an array or list")

    if action in stack_operations and obj != "stack":
        return err(f"Semantic Error: '{action}' operation requires a stack")

    if action in queue_operations and obj != "queue":
        return err(f"Semantic Error: '{action}' operation requires a queue")

    return ok("Semantic Analysis Passed")



def ir_generator(structure):
    return {
        "actor":           structure["ACTOR"],
        "action":          structure["ACTION"],
        "object":          structure["OBJECT"],
        "input_type":      structure["ATTRIBUTE"],
        "condition":       structure["CONDITION"],
        "expected_result": structure["OUTCOME"],
    }



def _tc(id_, input_, output):
    """Convenience constructor for a test case dict."""
    return {"Test Case ID": id_, "Input": input_, "Expected Output": output}

def _fmt_ll(lst):
    if not lst:
        return "NULL"
    return " → ".join(map(str, lst)) + " → NULL"

def _fmt_stack(stack):
    if not stack:
        return "Stack is Empty"
    width  = 7
    out    = "        Top\n"
    out   += "   ┌" + "─" * width + "┐\n"
    for e in reversed(stack):
        out += f"   │ {str(e).center(width - 2)} │\n"
    out   += "   └" + "─" * width + "┘\n"
    return out

def _fmt_queue(queue):
    if not queue:
        return "Queue is Empty"
    return "Front → " + " ".join(f"[ {e} ]" for e in queue) + " ← Rear"


def _gen_max_array(_):
    tcs = []
    for i, arr in enumerate([
        [random.randint(0,  50) for _ in range(random.randint(3,6))],
        [random.randint(-50, -1) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50)],
    ], 1):
        tcs.append(_tc(f"TC_{i:02d}", str(arr), str(max(arr))))
    tcs.append(_tc("TC_05", "Empty Array []", "Error: No elements in array"))
    return tcs

def _gen_min_array(_):
    tcs = []
    for i, arr in enumerate([
        [random.randint(0,  50) for _ in range(random.randint(3,6))],
        [random.randint(-50, -1) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50)],
    ], 1):
        tcs.append(_tc(f"TC_{i:02d}", str(arr), str(min(arr))))
    tcs.append(_tc("TC_05", "Empty Array []", "Error: No elements in array"))
    return tcs

def _gen_sum_array(_):
    tcs = []
    for i, arr in enumerate([
        [random.randint(0,  50) for _ in range(random.randint(3,6))],
        [random.randint(-50, -1) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50)],
    ], 1):
        tcs.append(_tc(f"TC_{i:02d}", str(arr), str(sum(arr))))
    tcs.append(_tc("TC_05", "[]", "0"))
    return tcs

def _gen_reverse_array(_):
    tcs = []
    for i, arr in enumerate([
        [random.randint(0,  50) for _ in range(random.randint(3,6))],
        [random.randint(-50, -1) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50)],
    ], 1):
        tcs.append(_tc(f"TC_{i:02d}", str(arr), str(arr[::-1])))
    tcs.append(_tc("TC_05", "[]", "Error: No element in array"))
    return tcs

def _gen_size_array(_):
    tcs = []
    for i, arr in enumerate([
        [random.randint(0, 50) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50) for _ in range(random.randint(10,16))],
        [random.randint(-50, 50)],
    ], 1):
        tcs.append(_tc(f"TC_{i:02d}", str(arr), str(len(arr))))
    tcs.append(_tc("TC_05", "[]", "Error: No element in array"))
    return tcs

def _gen_sort_array(_):
    tcs = []
    for i, arr in enumerate([
        [random.randint(0, 50)  for _ in range(random.randint(3,6))],
        [random.randint(-50, 0) for _ in range(random.randint(3,6))],
        [random.randint(-50, 50) for _ in range(random.randint(10,16))],
        [random.randint(-50, 50)],
    ], 1):
        tcs.append(_tc(f"TC_{i:02d}", str(arr), str(sorted(arr))))
    tcs.append(_tc("TC_05", "[]", "Error: No element in array"))
    return tcs

def _gen_ll_insert(_):
    ll  = [random.randint(-50, 50) for _ in range(random.randint(3,6))]
    val = random.randint(1, 50)
    tcs = []

    h = ll.copy(); h.insert(0, val)
    tcs.append(_tc("TC_01", f"List={_fmt_ll(ll)}, Insert {val} at head", _fmt_ll(h)))

    t = ll.copy(); t.append(val)
    tcs.append(_tc("TC_02", f"List={_fmt_ll(ll)}, Insert {val} at tail", _fmt_ll(t)))

    pos = random.randint(1, len(ll) - 1)
    m = ll.copy(); m.insert(pos, val)
    tcs.append(_tc("TC_03", f"List={_fmt_ll(ll)}, Insert {val} at pos {pos}", _fmt_ll(m)))

    tcs.append(_tc("TC_04", f"List=NULL, Insert {val}", _fmt_ll([val])))
    tcs.append(_tc("TC_05", f"List={_fmt_ll(ll)}, Insert {val} at pos {len(ll)+5}",
                   "Error: Position out of bounds"))
    return tcs

def _gen_ll_delete(_):
    ll  = [random.randint(1, 50) for _ in range(5)]
    pos = random.randint(0, len(ll) - 1)
    after = ll.copy(); after.pop(pos)
    return [
        _tc("TC_01", f"{_fmt_ll(ll)}, Delete node at pos {pos}", _fmt_ll(after)),
        _tc("TC_02", "Delete from empty list", "Error: List Empty"),
    ]

def _gen_stack_push(_):
    stack = []
    tcs   = []
    for i in range(1, 6):
        v = random.randint(1, 50)
        stack.append(v)
        tcs.append(_tc(f"TC_{i:02d}", f"Push {v} into stack", _fmt_stack(stack.copy())))
    tcs.append(_tc("TC_06", "Push element into full stack", "Stack Overflow"))
    return tcs

def _gen_stack_pop(_):
    stack = [random.randint(1, 50) for _ in range(5)]
    tcs   = [_tc("TC_00", "Initial Stack", _fmt_stack(stack.copy()))]
    for i in range(1, 6):
        popped = stack.pop()
        tcs.append(_tc(f"TC_{i:02d}", "Pop element from stack",
                       f"Popped Element: {popped}\n\nStack After Pop:\n{_fmt_stack(stack.copy())}"))
    tcs.append(_tc("TC_06", "Pop element from empty stack", "Stack Underflow"))
    return tcs

def _gen_queue_enqueue(_):
    queue = []
    tcs   = []
    for i in range(1, 6):
        v = random.randint(1, 50)
        queue.append(v)
        tcs.append(_tc(f"TC_{i:02d}", f"Enqueue {v} into queue", _fmt_queue(queue.copy())))
    tcs.append(_tc("TC_06", "Enqueue element into full queue", "Queue Overflow"))
    return tcs

def _gen_queue_dequeue(_):
    queue = [random.randint(1, 50) for _ in range(5)]
    tcs   = [_tc("TC_00", "Initial Queue", _fmt_queue(queue.copy()))]
    for i in range(1, 6):
        removed = queue.pop(0)
        tcs.append(_tc(f"TC_{i:02d}", "Dequeue element from queue",
                       f"Removed Element: {removed}\n\nQueue After Dequeue:\n{_fmt_queue(queue.copy())}"))
    tcs.append(_tc("TC_06", "Dequeue element from empty queue", "Queue Underflow"))
    return tcs

def _gen_password(_):
    return [
        _tc("TC_01", generate_valid_password(), "Password Accepted"),
        _tc("TC_02", generate_invalid_password(),
            "Password must contain uppercase and special characters"),
        _tc("TC_03", generate_short_password(), "Password too short"),
        _tc("TC_04", generate_long_password(),  "Password too long"),
        _tc("TC_05", " ", "Password Required"),
    ]

def _gen_login(_):
    return [
        _tc("TC_01", "Username ''",             "Username Required"),
        _tc("TC_02", "Password ''",             "Password Required"),
        _tc("TC_03", "Username '' Password ''", "Credentials Required"),
        _tc("TC_04", "5 Wrong Passwords",       "Account Blocked"),
        _tc("TC_05", "Correct Password After Lock", "Access Denied"),
        _tc("TC_06", "Correct Password Before Limit", "Login Success"),
    ]

def _gen_file_upload(_):
    valid_ext = ["pdf", "png", "jpg", "jpeg"]
    danger    = ["exe", "php", "bat"]
    valid_f   = f"file{random.randint(1,100)}.{random.choice(valid_ext)}"
    bad_f     = f"file{random.randint(1,100)}.{random.choice(danger)}"
    large_f   = f"large_file_{random.randint(100,500)}MB.zip"
    return [
        _tc("TC_01", valid_f,        "Upload Success"),
        _tc("TC_02", bad_f,          "Invalid file type"),
        _tc("TC_03", " ",            "No file selected"),
        _tc("TC_04", large_f,        "File size exceeds limit"),
        _tc("TC_05", "image.jpg.exe","Suspicious file detected"),
    ]


def _gen_heap_insert(_):
    import heapq
    heap = []
    tcs  = []
    for i in range(1, 6):
        v = random.randint(1, 50)
        heapq.heappush(heap, v)
        tcs.append(_tc(f"TC_{i:02d}", f"Insert {v} into min-heap",
                       f"Heap: {heap}  |  Min: {heap[0]}"))
    tcs.append(_tc("TC_06", "Insert into full heap", "Heap Overflow"))
    return tcs

def _gen_heap_extract(_):
    import heapq
    heap = [random.randint(1, 50) for _ in range(5)]
    heapq.heapify(heap)
    tcs  = [_tc("TC_00", "Initial heap", f"Heap: {heap}  |  Min: {heap[0]}")]
    for i in range(1, 6):
        if heap:
            extracted = heapq.heappop(heap)
            tcs.append(_tc(f"TC_{i:02d}", "Extract min from heap",
                           f"Extracted: {extracted}  |  Remaining: {heap}"))
    tcs.append(_tc("TC_06", "Extract from empty heap", "Error: Heap is empty"))
    return tcs


def _gen_tree_insert(_):
    vals = random.sample(range(1, 100), 5)
    tcs  = []
    inserted = []
    for i, v in enumerate(vals, 1):
        inserted.append(v)
        tcs.append(_tc(f"TC_{i:02d}", f"Insert {v} into BST",
                       f"Inserted nodes so far: {inserted}"))
    tcs.append(_tc("TC_06", "Insert duplicate value", "Duplicate: value already exists"))
    return tcs

def _gen_tree_search(_):
    vals   = sorted(random.sample(range(1, 100), 6))
    target = random.choice(vals)
    absent = random.choice([x for x in range(1, 100) if x not in vals])
    return [
        _tc("TC_01", f"Search {target} in BST {vals}", f"Found: {target}"),
        _tc("TC_02", f"Search {absent} in BST {vals}", "Not Found"),
        _tc("TC_03", "Search in empty BST",            "Error: Tree is empty"),
        _tc("TC_04", f"Search root {vals[len(vals)//2]}", "Found at root"),
        _tc("TC_05", f"Search leaf {vals[0]}",         "Found at leaf node"),
    ]

def _gen_tree_traversal(_):
    vals = sorted(random.sample(range(1, 50), 5))
    return [
        _tc("TC_01", f"Inorder traversal of BST {vals}",   str(vals)),
        _tc("TC_02", f"Preorder traversal of BST {vals}",  f"Root first: {vals[len(vals)//2]}"),
        _tc("TC_03", f"Postorder traversal of BST {vals}", f"Root last: {vals[len(vals)//2]}"),
        _tc("TC_04", "Traversal on empty tree",             "Empty Tree"),
        _tc("TC_05", "Traversal on single-node tree",       "Single node returned"),
    ]


def _gen_graph_search(_):
    return [
        _tc("TC_01", "BFS from node A in connected graph", "Visited: A B C D (level order)"),
        _tc("TC_02", "DFS from node A in connected graph", "Visited: A B D C (depth first)"),
        _tc("TC_03", "BFS/DFS on disconnected graph",      "Only reachable nodes visited"),
        _tc("TC_04", "BFS/DFS on single node",             "Visited: [node]"),
        _tc("TC_05", "BFS/DFS on empty graph",             "Error: Graph is empty"),
    ]



_HANDLERS = [
    (lambda r: "max"  in r and "array" in r,                     _gen_max_array),
    (lambda r: "min"  in r and "array" in r,                     _gen_min_array),
    (lambda r: "sum"  in r and "array" in r,                     _gen_sum_array),
    (lambda r: "reverse" in r and "array" in r,                  _gen_reverse_array),
    (lambda r: ("size" in r or "length" in r) and "array" in r,  _gen_size_array),
    (lambda r: "sort" in r and "array" in r,                     _gen_sort_array),
    (lambda r: "linked list" in r and "insert" in r,             _gen_ll_insert),
    (lambda r: "linked list" in r and ("remove" in r or "delete" in r), _gen_ll_delete),
    (lambda r: "stack" in r and "push" in r,                     _gen_stack_push),
    (lambda r: "stack" in r and "pop"  in r,                     _gen_stack_pop),
    (lambda r: "queue" in r and ("enqueue" in r or "add" in r),  _gen_queue_enqueue),
    (lambda r: "queue" in r and "dequeue" in r,                  _gen_queue_dequeue),
    (lambda r: "heap" in r and "insert" in r,                    _gen_heap_insert),
    (lambda r: "heap" in r and ("extract" in r or "remove" in r or "pop" in r), _gen_heap_extract),
    (lambda r: "tree" in r and "insert" in r,                    _gen_tree_insert),
    (lambda r: "tree" in r and "search" in r,                    _gen_tree_search),
    (lambda r: "tree" in r and "traversal" in r,                 _gen_tree_traversal),
    (lambda r: "graph" in r and ("search" in r or "bfs" in r or "dfs" in r), _gen_graph_search),
    (lambda r: "password" in r,                                  _gen_password),
    (lambda r: "login"    in r,                                  _gen_login),
    (lambda r: "upload"   in r and "file" in r,                  _gen_file_upload),
]


def generate_test_cases(ir, requirement):
    req_lower = requirement.lower()
    for predicate, handler in _HANDLERS:
        if predicate(req_lower):
            return handler(ir)
    return []


import streamlit as st

st.set_page_config(
    page_title="NLP Test Case Generator",
    page_icon="🧪",
    layout="wide",
)

st.markdown("""
<style>
.stApp { background-color:#f4f6f9; color:#1f2933; font-family:"Segoe UI",sans-serif; }
h1 { color:#0f172a; font-weight:700; }
h2,h3 { color:#1e293b; font-weight:600; }
.stTextInput>div>div>input {
    background-color:#ffffff; color:#1f2933;
    border:1px solid #d1d5db; border-radius:8px; padding:6px;
}
.stButton button {
    background-color:#2563eb; color:white;
    border-radius:8px; border:none; font-weight:600; padding:6px 14px;
}
.stButton button:hover { background-color:#1d4ed8; }
.stTable table { background-color:white; border-radius:8px; border-collapse:collapse; }
.stTable th { background-color:#e2e8f0; color:#1f2933; font-weight:600; }
.stTable td { color:#1f2933; }
pre { background-color:#eef2f7!important; color:#1f2933!important; border-radius:6px; padding:10px; }
.stAlert { border-radius:8px; }
[data-testid="stSidebar"] { background-color:#e9eef5; }
[data-testid="stJson"],.stJson {
    background-color:#ffffff!important; border-radius:8px!important;
    padding:10px!important; color:#000000!important;
}
[data-testid="stJson"] span,[data-testid="stJson"] * { color:#000000!important; }
[data-testid="stVegaLiteChart"] {
    background-color:#ffffff!important; border-radius:8px!important; padding:10px!important;
}
[data-testid="stVegaLiteChart"] text,
[data-testid="stVegaLiteChart"] svg text { fill:#000000!important; color:#000000!important; }
[data-testid="stDataFrame"],
[data-testid="stDataFrame"]>div,
[data-testid="stDataFrameResizable"] {
    background-color:#ffffff!important; color:#000000!important; border-radius:8px!important;
}
[data-testid="stDataFrame"] canvas { filter:invert(1) hue-rotate(180deg)!important; }
[data-testid="stMarkdownContainer"] code,
[data-testid="stText"] code,.stMarkdown code {
    background-color:#e8edf3!important; color:#000000!important;
    border-radius:4px!important; padding:2px 6px!important;
}
</style>
""", unsafe_allow_html=True)

st.title("🧪 NLP Test Case Generator")

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("Recent Requirements")
    if st.session_state.history:
        for prev in reversed(st.session_state.history[-5:]):
            if st.button(prev, key=f"hist_{prev}"):
                st.session_state["prefill"] = prev
    else:
        st.info("Your last 5 requirements will appear here.")

prefill      = st.session_state.pop("prefill", "")
requirement  = st.text_input(
    "Enter Requirement",
    value=prefill,
    max_chars=500,
    help="Max 500 characters. Example: 'find max of array'",
)

col1, col2 = st.columns([1, 5])
with col1:
    generate = st.button("Generate Test Cases")

if generate:
    if not requirement.strip():
        st.error("Please enter a requirement before generating.")
        st.stop()

    if requirement not in st.session_state.history:
        st.session_state.history.append(requirement)

    risks = detect_security_risk(requirement)
    if risks:
        st.subheader("⚠ Security Risk Detection")
        security_tcs = []
        for r in risks:
            st.warning(f"⚠ {r}")
            if r == "SQL Injection Risk":
                security_tcs.append(_tc("SEC_TC_01", "username=' OR '1'='1", "Login rejected"))
            if r == "Unauthorized Access Risk":
                security_tcs.append(_tc("SEC_TC_02", "Guest accessing admin panel", "Access Denied"))
            if r == "File Upload Attack Risk":
                security_tcs.append(_tc("SEC_TC_03", "Upload .exe file", "File rejected"))
        if security_tcs:
            st.subheader("Security Test Cases")
            st.table(pd.DataFrame(security_tcs))

    tracker = EmissionsTracker(log_level="error")
    tracker.start()

    cpu_start    = psutil.cpu_percent(interval=0.1)   # FIX: primed reading
    memory_start = psutil.virtual_memory().percent

    try:
        t0         = time.perf_counter()
        lex_result = lexical_analyzer(requirement)
        lex_time   = time.perf_counter() - t0

        st.subheader("1️⃣  Lexical Analysis")
        if is_err(lex_result):
            st.error(lex_result["error"])
            st.error("Compilation stopped due to Lexical Error.")
            st.stop()

        lex_data  = lex_result["data"]
        structure = lex_data["structure"]
        coverage  = lex_data["coverage"]

        st.write("**Tokens:**")
        st.code(lex_data["tokens"])
        st.write("**Lexical Structure:**")
        st.json(structure)

        st.write("**Requirement Coverage Score:**")
        st.progress(coverage / 100, text=f"{coverage}% of semantic fields detected")
        if coverage < 60:
            st.warning("Low coverage — consider specifying ACTOR, ATTRIBUTE or OUTCOME "
                       "for richer test cases.")

        t0            = time.perf_counter()
        syntax_result = syntax_analyzer(structure, requirement)
        syntax_time   = time.perf_counter() - t0

        st.subheader("2️⃣  Syntax Analysis")
        if is_err(syntax_result):
            st.error(syntax_result["error"])
            st.error("Compilation stopped due to Syntax Error.")
            st.stop()

        for key, value in syntax_result["data"].items():
            st.write(f"**{key}:** {value}")

        t0              = time.perf_counter()
        semantic_result = semantic_analyzer(structure)
        semantic_time   = time.perf_counter() - t0

        st.subheader("3️⃣  Semantic Analysis")
        if is_err(semantic_result):
            st.error(semantic_result["error"])
            st.error("Compilation stopped due to Semantic Error.")
            st.stop()

        st.success(semantic_result["data"])

        t0      = time.perf_counter()
        ir      = ir_generator(structure)
        ir_time = time.perf_counter() - t0

        st.subheader("4️⃣  Intermediate Representation")
        ir_display = {k: (v if v else "None") for k, v in ir.items()}
        st.table(pd.DataFrame(ir_display.items(), columns=["Field", "Value"]))

        t0              = time.perf_counter()
        test_cases      = generate_test_cases(ir, requirement)
        test_cases_time = time.perf_counter() - t0

        st.subheader("5️⃣  Generated Test Cases")

        if not test_cases:
            st.warning(
                "No test case template matched this requirement.\n\n"
                "Supported: max/min/sum/reverse/sort/size on array, "
                "linked list insert/delete, stack push/pop, queue enqueue/dequeue, "
                "heap insert/extract, tree insert/search/traversal, "
                "graph search/BFS/DFS, password, login, file upload."
            )
        else:
            all_tc_rows = []
            for i, tc in enumerate(test_cases, 1):
                st.write(f"### Test Case {i}")
                for key, value in tc.items():
                    if key == "Expected Output":
                        st.write(f"**{key}:**")
                        st.code(value)
                    else:
                        st.write(f"**{key}:** {value}")
                all_tc_rows.append(tc)

            df_dl = pd.DataFrame(all_tc_rows)
            st.download_button(
                label="⬇ Download Test Cases as CSV",
                data=df_dl.to_csv(index=False).encode("utf-8"),
                file_name="test_cases.csv",
                mime="text/csv",
            )

    finally:
        try:
            emissions = tracker.stop()
        except Exception:
            emissions = 0.0

    cpu_end    = psutil.cpu_percent(interval=None)
    memory_end = psutil.virtual_memory().percent

    st.subheader("🌱 Green Compiler Metrics")

    st.subheader("Carbon Emission Indicator")
    st.write(f"Carbon Emissions (kg CO₂): `{emissions:.8f}`")
    if emissions < 0.001:
        st.success("🟢 Very Low Carbon Emission")
    elif emissions < 0.01:
        st.warning("🟡 Moderate Carbon Emission")
    else:
        st.error("🔴 High Carbon Emission")

    energy = max(cpu_end - cpu_start, 0) * 0.001
    st.write(f"Estimated Energy Consumption (kWh): `{energy:.6f}`")

    memory_delta = memory_end - memory_start
    st.write(f"Memory Usage Change: `{memory_delta:+.1f}%`")

    data = {
        "Stage": ["Lexical", "Syntax", "Semantic", "IR", "Test Case"],
        "Execution Time (ms)": [
            lex_time   * 1000,
            syntax_time   * 1000,
            semantic_time * 1000,
            ir_time       * 1000,
            test_cases_time * 1000,
        ],
    }
    df_time = pd.DataFrame(data)
    st.subheader("⏱ Execution Time Analysis (milliseconds)")
    st.bar_chart(df_time.set_index("Stage"))
