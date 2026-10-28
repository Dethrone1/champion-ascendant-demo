from pathlib import Path

from flask import Flask, abort, jsonify, redirect, request, send_from_directory

from scoring import service

app = Flask(__name__)

PAGES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

# Live pages. Each is reachable at /name and /name.html.
PAGES = {"index", "calculator", "both", "methodology", "build"}

# Retired pages point to the page that replaced them, so old links keep working.
RETIRED = {"prospects": "both", "dwcs": "both", "receipts": "index"}


def serve_page(name):
    # Pages are plain HTML, sent as-is (not through Jinja).
    return send_from_directory(PAGES_DIR, f"{name}.html")


@app.route("/")
def home():
    return serve_page("index")


@app.route("/og-card.png")
def og_card():
    return send_from_directory(STATIC_DIR, "og-card.png")


# ---------- JSON API: scoring happens here, never in the browser ----------

@app.get("/api/options")
def api_options():
    return jsonify(service.options())


@app.post("/api/score")
def api_score():
    try:
        fighter = service.parse_request(request.get_json(silent=True) or {})
    except service.InputError as e:
        return jsonify(error=str(e)), 400
    return jsonify(service.score_both(fighter))


@app.get("/api/board")
def api_board():
    return jsonify(service.board())


@app.route("/<path:slug>")
def page(slug):
    name = slug[:-5] if slug.endswith(".html") else slug
    if name in RETIRED:
        return redirect(f"/{RETIRED[name]}.html" if RETIRED[name] != "index" else "/", code=301)
    if name in PAGES:
        return serve_page(name)
    abort(404)


if __name__ == "__main__":
    app.run(debug=True)
