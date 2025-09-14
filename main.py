import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/")
def root():
    return jsonify(ok=True, service="ottomate-health", path="/")

@app.get("/health")
def health():
    return jsonify(ok=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
