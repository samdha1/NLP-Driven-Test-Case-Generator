"""
Flask backend for NLP-Driven Test Case Generator web frontend.
Serves the UI and provides POST /api/generate for spec + test case generation.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from pipeline_api import run_pipeline

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    requirement = (data.get("requirement") or "").strip()
    code = (data.get("code") or "").strip()

    if not requirement:
        return jsonify({"error": "Missing requirement"}), 400

    try:
        result = run_pipeline(requirement, code=code or None)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "spec": None, "test_cases": []}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
