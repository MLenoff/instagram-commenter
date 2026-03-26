from flask import Flask, request, jsonify
import os
import requests as req
import json as _json

app = Flask(__name__)

API_SECRET    = os.environ.get("API_SECRET", "")
IG_SESSION_ID = os.environ.get("IG_SESSION_ID", "")
IG_CSRF_TOKEN = os.environ.get("IG_CSRF_TOKEN", "")
IG_DID        = os.environ.get("IG_DID", "")
IG_MID        = os.environ.get("IG_MID", "")

IG_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

def shortcode_to_media_id(shortcode):
    media_id = 0
    for char in shortcode:
        media_id = media_id * 64 + IG_ALPHABET.index(char)
    return media_id

@app.route("/comment", methods=["POST"])
def post_comment():
    secret = request.headers.get("X-API-Secret", "")
    if API_SECRET and secret != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = _json.loads(request.get_data(as_text=True) or "{}")
    except Exception:
        data = {}
    short_code = data.get("short_code")
    comment    = data.get("comment")

    if not short_code or not comment:
        return jsonify({"error": "short_code and comment are required"}), 400

    if not IG_SESSION_ID:
        return jsonify({"error": "IG_SESSION_ID not configured"}), 500

    try:
        media_id = shortcode_to_media_id(short_code)

        cookie_parts = [
            f"sessionid={IG_SESSION_ID}",
            f"csrftoken={IG_CSRF_TOKEN}",
        ]
        if IG_DID:
            cookie_parts.append(f"ig_did={IG_DID}")
        if IG_MID:
            cookie_parts.append(f"mid={IG_MID}")
        cookie_str = "; ".join(cookie_parts)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "X-CSRFToken": IG_CSRF_TOKEN,
            "Cookie": cookie_str,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/p/{short_code}/",
            "Origin": "https://www.instagram.com",
        }

        resp = req.post(
            f"https://www.instagram.com/api/v1/web/comments/{media_id}/add/",
            headers=headers,
            data={"comment_text": comment},
            timeout=10,
            allow_redirects=False
        )

        if resp.status_code == 200:
            return jsonify({"success": True, "short_code": short_code})
        else:
            return jsonify({"error": f"Instagram API error {resp.status_code}: {resp.text[:300]}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/echo", methods=["POST"])
def echo():
    raw = request.get_data(as_text=True)
    return jsonify({"received": raw, "content_type": request.content_type, "headers": dict(request.headers)})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "session_configured": bool(IG_SESSION_ID)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
