"""
URL Shortener REST API - in-memory storage, port 8080.
"""

import os
import re
import string
import random
from datetime import datetime, timezone
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

# In-memory store: short_code -> {original_url, access_count, created_at}
_store = {}
# Reverse: custom_code already used
_codes_used = set()

# Config
PORT = int(os.environ.get("PORT", 8080))
MAX_URL_LENGTH = 2000
SHORT_CODE_LENGTH = 6
VALID_SCHEMES = ("http", "https")


def _validate_url(url):
    """Validate URL: non-empty, http/https, max length."""
    if not url or not isinstance(url, str):
        return False, "URL is required"
    url = url.strip()
    if not url:
        return False, "URL is required"
    if len(url) > MAX_URL_LENGTH:
        return False, "URL too long"
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme.lower() not in VALID_SCHEMES:
            return False, "URL must use HTTP or HTTPS"
        if not parsed.netloc:
            return False, "Invalid URL"
    except Exception:
        return False, "Invalid URL"
    return True, url


def _generate_short_code():
    """Generate 6-8 alphanumeric short code."""
    length = random.randint(6, 8)
    chars = string.ascii_letters + string.digits
    while True:
        code = "".join(random.choices(chars, k=length))
        if code not in _store:
            return code


@app.route("/")
def index():
    """Health/root - for server check."""
    return jsonify({"status": "ok", "service": "url-shortener"}), 200


@app.route("/urls", methods=["POST"])
def create_url():
    """Create a new short URL. Body: {"url": "...", "custom_code": "..."} (optional)."""
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    url = data.get("url")
    valid, result = _validate_url(url)
    if not valid:
        return jsonify({"error": result}), 400
    url = result
    custom_code = data.get("custom_code")
    if custom_code is not None:
        custom_code = str(custom_code).strip()
        if not re.match(r"^[a-zA-Z0-9]{6,8}$", custom_code):
            return jsonify({"error": "Custom code must be 6-8 alphanumeric characters"}), 400
        if custom_code in _store:
            return jsonify({"error": "Short code already in use"}), 409
        short_code = custom_code
        _codes_used.add(short_code)
    else:
        short_code = _generate_short_code()
    _store[short_code] = {
        "original_url": url,
        "access_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify({
        "short_code": short_code,
        "original_url": url,
        "access_count": 0,
        "created_at": _store[short_code]["created_at"],
    }), 201


@app.route("/urls", methods=["GET"])
def list_urls():
    """List all shortened URLs."""
    items = []
    for code, data in _store.items():
        items.append({
            "short_code": code,
            "original_url": data["original_url"],
            "access_count": data["access_count"],
            "created_at": data["created_at"],
        })
    return jsonify(items), 200


@app.route("/urls/<short_code>/stats", methods=["GET"])
def get_stats(short_code):
    """Get stats for a short URL."""
    if short_code not in _store:
        return jsonify({"error": "Not found"}), 404
    data = _store[short_code]
    return jsonify({
        "short_code": short_code,
        "original_url": data["original_url"],
        "access_count": data["access_count"],
        "created_at": data["created_at"],
    }), 200


@app.route("/urls/<short_code>", methods=["DELETE"])
def delete_url(short_code):
    """Delete a short URL."""
    if short_code not in _store:
        return jsonify({"error": "Not found"}), 404
    del _store[short_code]
    _codes_used.discard(short_code)
    return "", 204


@app.route("/<short_code>", methods=["GET"])
def redirect_to_url(short_code):
    """Redirect to original URL by short code."""
    if short_code not in _store:
        return jsonify({"error": "Not found"}), 404
    data = _store[short_code]
    data["access_count"] += 1
    return redirect(data["original_url"], code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
