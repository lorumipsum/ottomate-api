import os, json, logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.get("/")
def root():
    rev = os.getenv("K_REVISION", "unknown")
    return jsonify(ok=True, service="ottomate-health", path="/", revision=rev)

@app.get("/health")
def health():
    return jsonify(ok=True)

@app.get("/version")
def version():
    return jsonify(
        ok=True,
        revision=os.getenv("K_REVISION","unknown"),
        project=os.getenv("GOOGLE_CLOUD_PROJECT","unknown")
    )

@app.post("/echo")
def echo():
    if not request.is_json:
        return jsonify(ok=False, error="Expected application/json"), 400
    body = request.get_json(silent=True)
    if body is None:
        return jsonify(ok=False, error="Invalid JSON"), 400
    app.logger.info("echo payload=%s", json.dumps(body)[:2000])
    return jsonify(ok=True, received=body)

# Error handlers
@app.errorhandler(400)
def bad_request(e):
    return jsonify(ok=False, error="bad_request"), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify(ok=False, error="not_found"), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
