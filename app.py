from flask import Flask, request, jsonify
from instagrapi import Client
import os
import threading

app = Flask(__name__)

IG_USERNAME = os.environ.get("IG_USERNAME")
IG_PASSWORD = os.environ.get("IG_PASSWORD")
API_SECRET  = os.environ.get("API_SECRET", "")

cl = Client()
logged_in = False
login_error = None

def background_login():
    global logged_in, login_error
    try:
        print(f"Attempting Instagram login for {IG_USERNAME}...")
        cl.login(IG_USERNAME, IG_PASSWORD)
        logged_in = True
        print("Instagram login successful!")
    except Exception as e:
        login_error = str(e)
        print(f"Instagram login failed: {e}")

# Start login immediately when the app loads
login_thread = threading.Thread(target=background_login, daemon=True)
login_thread.start()

@app.route("/comment", methods=["POST"])
def post_comment():
    secret = request.headers.get("X-API-Secret", "")
    if API_SECRET and secret != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    if login_error:
        return jsonify({"error": f"Instagram login failed: {login_error}"}), 500

    if not logged_in:
        return jsonify({"error": "Instagram login in progress, please retry in 30 seconds"}), 503

    data = request.get_json(force=True, silent=True) or {}
    short_code = data.get("short_code")
    comment    = data.get("comment")

    if not short_code or not comment:
        return jsonify({"error": "short_code and comment are required"}), 400

    try:
        media_id = cl.media_pk_from_code(short_code)
        cl.media_comment(media_id, comment)
        return jsonify({"success": True, "short_code": short_code})
    except Exception as e:
        global logged_in
        logged_in = False
        # Retry login in background
        t = threading.Thread(target=background_login, daemon=True)
        t.start()
        return jsonify({"error": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "logged_in": logged_in,
        "login_error": login_error
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
