"""Smoke tests for the pages: everything serves, old URLs redirect, and no page
shows raw code, version numbers or formula files."""
import re

from app import app, PAGES, RETIRED

STATIC = ["/static/site.css", "/static/site.js", "/static/favicon.svg", "/og-card.png", "/robots.txt"]


def visible_text(html):
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", html)


def pages():
    c = app.test_client()
    for name in PAGES:
        yield name, c.get("/" if name == "index" else f"/{name}").get_data(as_text=True)


def test_pages_and_assets_serve():
    c = app.test_client()
    for name in PAGES:
        for url in (("/",) if name == "index" else (f"/{name}", f"/{name}.html")):
            assert c.get(url).status_code == 200, url
    for url in STATIC:
        assert c.get(url).status_code == 200, url
    assert c.get("/not-a-page").status_code == 404


def test_retired_pages_redirect():
    c = app.test_client()
    for old in RETIRED:
        assert c.get(f"/{old}").status_code == 301, old


def test_no_code_or_versions_on_pages():
    for name, html in pages():
        assert html.count("<script") == html.count("</script>"), f"{name}: unbalanced script tags"
        text = visible_text(html)
        for tell in ("function (", "function(", "innerHTML", "=>", "});"):
            assert tell not in text, f"{name}: code visible on the page ({tell!r})"
        assert not re.search(r"\bv\d+\.\d", html), f"{name}: shows a version number"


def test_formula_never_reaches_the_browser():
    c = app.test_client()
    for url in ("/static/ascent.js", "/static/ascent_tables.js", "/static/both_systems.json"):
        assert c.get(url).status_code == 404, url
    for name, html in pages():
        assert "ascent_tables" not in html and "/static/ascent.js" not in html, name


def test_page_scripts_parse():
    """Every inline script is valid JavaScript (needs Node.js; skipped without it)."""
    import shutil
    import subprocess
    import tempfile

    import pytest

    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    for name, html in pages():
        for i, js in enumerate(re.findall(r"<script>(.*?)</script>", html, flags=re.S)):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(js)
            r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
            assert r.returncode == 0, f"{name} script {i}: {r.stderr.strip()[:300]}"
    r = subprocess.run([node, "--check", "static/site.js"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_link_preview_tags():
    """Instagram and others need an absolute image URL with its size to show a preview."""
    for name, html in pages():
        for tag in ('property="og:image" content="https://www.championascendant.com/og-card.png"',
                    'property="og:image:width" content="1200"', 'property="og:image:height" content="630"'):
            assert tag in html, f"{name}: missing {tag}"
    assert "Disallow: /" not in app.test_client().get("/robots.txt").get_data(as_text=True)
