from pathlib import Path

from flask import Flask, abort, redirect, send_from_directory

app = Flask(__name__)

PAGES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

# Live pages. Each is reachable at /name and /name.html.
PAGES = {"index", "both", "receipts", "methodology"}

# Retired pages (removed 24 Oct 2026) point to the page that replaced them,
# so old links and shared URLs keep working.
RETIRED = {"prospects": "both", "dwcs": "both"}


def serve_page(name):
    # Pages are plain HTML, sent as-is (not through Jinja).
    return send_from_directory(PAGES_DIR, f"{name}.html")


@app.route("/")
def home():
    return serve_page("index")


@app.route("/og-card.png")
def og_card():
    return send_from_directory(STATIC_DIR, "og-card.png")


@app.route("/<path:slug>")
def page(slug):
    name = slug[:-5] if slug.endswith(".html") else slug
    if name in RETIRED:
        return redirect(f"/{RETIRED[name]}.html", code=301)
    if name in PAGES:
        return serve_page(name)
    abort(404)


if __name__ == "__main__":
    app.run(debug=True)
