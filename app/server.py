import json
import os
from flask import Flask, request, jsonify
from app.lint_runner import lint

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.get("/schema")
def schema():
    """Serve the Blueprint JSON Schema"""
    try:
        # Load the schema from the root directory
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blueprint-schema.json')
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        return jsonify(schema)
    except FileNotFoundError:
        return jsonify({"error": "Blueprint schema not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in schema file"}), 500

@app.post("/lint")
def lint_endpoint():
    try:
        bp = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON body"}), 400
    result = lint(bp or {})
    status = 200 if result["ok"] else 422
    return jsonify(result), status

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
