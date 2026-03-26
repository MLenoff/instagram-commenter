from flask import Flask, request, jsonify
from instagrapi import Client
import os

app = Flask(__name__)

IG_USERNAME = os.environ.get("IG_USERNAME")
IG_PASSWORD = os.environ.get("IG_PASSWORD")
API_SECRET  = os.environ.get("API_SECRET", "")

cl = Client()
logged_in = False

def ensure_logged_in():
    global logged_in
    if not logged_in:
        cl.login(IG_USERNAME, IG_PASSWORD)
        logged_in = True

@app.route("/comment", methods=["POST"])
def post_comment():
    # Simple secret check so only N8N can call this
    secret = request.headers.get("X-API-Secret", "")
    if API_SECRET and secret != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True, silent=True) or {}
    short_code = data.get("short_code")
    comment    = data.get("comment")

    if not short_code or not comment:
        return jsonify({"error": "short_code and comment are required"}), 400

    try:
        ensure_logged_in()
        media_id = cl.media_pk_from_code(short_code)
        cl.media_comment(media_id, comment)
        return jsonify({"success": True, "short_code": short_code})
    except Exception as e:
        global logged_in
        logged_in = False  # Force re-login on next request
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
