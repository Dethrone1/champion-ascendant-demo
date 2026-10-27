"""Smoke tests for the Flask site: every page serves, old URLs redirect,
and no page shows raw script as visible text (the 24 Oct 2026 calculator bug)."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from app import app, PAGES, RETIRED  # noqa: E402

STATIC = ["/static/site.css", "/static/site.js", "/static/ascent.js",
          "/static/ascent_tables.js", "/static/both_systems.json", "/og-card.png"]


def visible_text(html):
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", html)


def test_pages_and_assets_serve():
    c = app.test_client()
    for name in PAGES:
        for url in (f"/{name}", f"/{name}.html") if name != "index" else ("/",):
            r = c.get(url)
            assert r.status_code == 200, url
    for url in STATIC:
        assert c.get(url).status_code == 200, url
    assert c.get("/not-a-page").status_code == 404


def test_retired_pages_redirect():
    c = app.test_client()
    for old, new in RETIRED.items():
        r = c.get(f"/{old}")
        assert r.status_code == 301 and r.headers["Location"].endswith(f"/{new}.html")


def test_no_script_leaks_into_page_text():
    c = app.test_client()
    for name in PAGES:
        html = c.get("/" if name == "index" else f"/{name}").get_data(as_text=True)
        assert html.count("<script") == html.count("</script>"), f"{name}: unbalanced script tags"
        text = visible_text(html)
        for tell in ("function (", "function(", "innerHTML", "=>", "});"):
            assert tell not in text, f"{name}: code visible on the page ({tell!r})"


if __name__ == "__main__":
    test_pages_and_assets_serve()
    test_retired_pages_redirect()
    test_no_script_leaks_into_page_text()
    print("OK - site smoke tests")
