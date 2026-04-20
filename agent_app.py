"""
Agentic AI Router — Flask server.
Serves the unified agent UI and provides classification + redirect API.
Runs on port 5001 (ShivTeja on 8501, NLP TestGen on 5000).
"""

import os
import sys
import json

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agent import classify

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)


@app.route("/")
def index():
    return send_from_directory("static", "agent_ui.html")


@app.route("/api/classify", methods=["POST"])
def api_classify():
    """
    Classify the requirement and return routing info.
    The frontend will redirect to the chosen project's URL with the requirement as a query param.
    """
    data = request.get_json() or {}
    requirement = (data.get("requirement") or "").strip()

    if not requirement:
        return jsonify({"error": "Please enter a requirement"}), 400

    try:
        result = classify(requirement)
        # Build redirect URL with requirement as query parameter
        redirect_url = result["url"] + "?requirement=" + _url_encode(requirement)
        result["redirect_url"] = redirect_url
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _url_encode(text: str) -> str:
    """Simple URL encoding."""
    import urllib.parse
    return urllib.parse.quote(text, safe="")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  AGENTIC AI ROUTER")
    print("  Powered by Llama 3.2 via Ollama")
    print("=" * 60)
    print("  Agent UI      -> http://localhost:5001")
    print("  ShivTeja      -> http://localhost:8501  (Streamlit)")
    print("  NLP TestGen   -> http://localhost:5000  (Flask)")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5001, debug=True)
