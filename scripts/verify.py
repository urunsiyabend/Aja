#!/usr/bin/env python3
"""Exercise the real CLI and validate generated artifacts with stdlib only."""
import json
from html.parser import HTMLParser
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import tomllib
from urllib.request import urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
COMPILER = shutil.which(os.environ.get("SIYO_BIN", "siyoc"))
if not COMPILER:
    raise SystemExit("Siyo compiler not found; set SIYO_BIN or add siyoc to PATH")
ENV = {**os.environ, "SIYO_BIN": COMPILER}


class ReadingAidsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.toc_links = []
        self.in_toc = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "nav" and "table-of-contents" in (attrs.get("class") or "").split():
            self.in_toc = True
        if tag == "a" and self.in_toc:
            self.toc_links.append(attrs.get("href") or "")

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_toc = False


def command(*args, cwd=ROOT, success=True):
    result = subprocess.run(args, cwd=cwd, env=ENV, text=True, capture_output=True, timeout=60)
    output = result.stdout + result.stderr
    if success:
        assert result.returncode == 0, output
        assert "Exception" not in output and "\tat " not in output, output
    else:
        assert result.returncode != 0, "Expected failure, got success:\n" + output
    return output


def verify_preview_server(project, flags_first=True):
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    with tempfile.TemporaryFile(dir=os.environ.get("TMPDIR")) as log:
        arguments = ["--drafts", str(port)] if flags_first else [str(port), "--drafts"]
        process = subprocess.Popen([str(project / "aja"), "serve", *arguments], cwd=project, env=ENV, stdout=log, stderr=log, start_new_session=True)
        try:
            deadline = time.monotonic() + 45
            while True:
                if process.poll() is not None:
                    log.seek(0)
                    raise AssertionError("Preview server exited: " + log.read().decode())
                try:
                    with urlopen(f"http://127.0.0.1:{port}/__aja/status", timeout=0.5) as response:
                        assert response.status == 200
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        log.seek(0)
                        raise AssertionError("Preview server did not start: " + log.read().decode())
                    time.sleep(0.1)
            with urlopen(f"http://127.0.0.1:{port}/posts/draft-example/", timeout=5) as response:
                assert response.status == 200, "serve --drafts must serve draft pages"
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)


def main():
    suite = command(COMPILER, "test")
    assert "Aja tests passed" in suite and "Aja configuration tests passed" in suite, suite
    assert "Table tests passed" in suite, suite
    for marker in ("Heading tests passed", "Metrics tests passed", "Navigation tests passed", "Presentation tests passed", "Task tests passed", "TOC settings tests passed", "Search index tests passed", "Archive tests passed"):
        assert marker in suite, suite
    scratch = os.environ.get("TMPDIR")
    with tempfile.TemporaryDirectory(prefix="aja-verify-", dir=scratch) as directory:
        project = Path(directory) / "site"
        shutil.copytree(ROOT, project, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
        shell = project / "templates/base.html"
        shell.write_text(shell.read_text() + "\n<!-- reading-context: {{toc}}|{{word_count}}|{{reading_time}}|{{post_navigation}}|{{previous_url}}|{{previous_title}}|{{next_url}}|{{next_title}} -->\n")
        version = tomllib.loads((project / "siyo.toml").read_text())["project"]["version"]
        assert f"aja {version} (Siyo 0.7.0)" in command(str(project / "aja"), "version", cwd=project)
        assert f"Aja {version}" in command(str(project / "aja"), "help", cwd=project)
        (project / "content/table-fixture.md").write_text(
            "---\ntitle: Table fixture\nkind: page\n---\n"
            "| Name | Value |\n| :--- | ---: |\n| **Aja** | <unsafe> |\n",
            encoding="utf-8",
        )
        (project / "content/task-fixture.md").write_text(
            "---\ntitle: Task fixture\nkind: page\ntoc: false\n---\n"
            "# Tasks\n\n- [ ] Write **docs** & <unsafe>\n- [x] Ship release\n",
            encoding="utf-8",
        )
        for slug, title, date, weight in (
            ("nav-older", "<Older> & post", "2026-09-29", 0),
            ("nav-middle", "Middle post", "2026-09-30", -100),
            ("nav-newer", "Newer post", "2026-10-01", 0),
        ):
            body = "## Getting started\n\n" + "word " * 201
            body += "\n\n## Getting started\n\n## Ürün Rehberi\n\n## Main\n\n```text\n# Hidden code heading\n```\n"
            (project / ("content/" + slug + ".md")).write_text(
                f"---\ntitle: {title}\ndate: {date}\nweight: {weight}\n---\n" + body,
                encoding="utf-8",
            )
        (project / "static/binary-fixture.bin").write_bytes(b"\x00\xff\xfe\x80binary\x00")
        command(str(project / "aja"), "check", cwd=project)
        command(str(project / "aja"), "build", cwd=project)
        output = project / "dist"
        for name in ("index.html", "feed.xml", "sitemap.xml", "robots.txt", "search.json", "about/index.html", "search/index.html", "archive/index.html", "archive/2026/09/index.html"):
            assert (output / name).is_file(), name
        for asset in (project / "static").rglob("*"):
            if asset.is_file():
                assert asset.read_bytes() == (output / asset.relative_to(project / "static")).read_bytes(), asset
        assert not (output / "posts/draft-example").exists(), "Draft leaked"
        month_body = (output / "archive/2026/09/index.html").read_text()
        assert month_body.index('/posts/nav-middle/') < month_body.index('/posts/nav-older/'), "Archive order is independent of weight"
        assert "&lt;Older&gt; &amp; post" in month_body and "<Older>" not in month_body
        assert '/archive/2026/09/' in (output / "archive/index.html").read_text()
        assert '/about/' not in month_body.split('<main id="main">')[1].split('</main>')[0], "Standalone pages must not become archive posts"
        search_index = json.loads((output / "search.json").read_text())
        indexed_post = next(item for item in search_index if item["url"] == "/posts/nav-middle/")
        assert "Hidden code heading" in indexed_post["content"] and "<h2" not in indexed_post["content"], "Search body contains visible/code text rather than HTML"
        search_page = (output / "search/index.html").read_text()
        assert 'id="search-form"' in search_page and 'id="search-query"' in search_page
        assert 'aria-live="polite"' in search_page and 'src="/search.js"' in search_page
        assert "{{" not in search_page and "{{" not in month_body
        ET.parse(output / "feed.xml")
        sitemap = ET.parse(output / "sitemap.xml")
        locations = [element.text or "" for element in sitemap.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        for route in ("/search/", "/archive/", "/archive/2026/09/"):
            assert any(location.endswith(route) for location in locations), "Missing discovery page in sitemap: " + route
        assert len(locations) == len(set(locations)), "Sitemap URLs must be unique"
        original_index = (output / "index.html").read_bytes()
        assert b'href="/search/"' in original_index and b'href="/archive/"' in original_index, "Default navigation exposes discovery pages"
        assert b"{{" not in original_index, "Generated indexes must resolve reading-aid placeholders"
        rendered_table = (output / "table-fixture/index.html").read_text()
        assert "<table>" in rendered_table and "<strong>Aja</strong>" in rendered_table, rendered_table
        assert "&lt;unsafe&gt;" in rendered_table and "<unsafe>" not in rendered_table, rendered_table
        rendered_post = (output / "posts/nav-middle/index.html").read_text()
        assert "2 min read" in rendered_post, rendered_post
        assert 'rel="prev" href="/posts/nav-older/"' in rendered_post, rendered_post
        assert 'rel="next" href="/posts/nav-newer/"' in rendered_post, rendered_post
        assert "&lt;Older&gt; &amp; post" in rendered_post and "<Older>" not in rendered_post, rendered_post
        parser = ReadingAidsParser()
        parser.feed(rendered_post)
        assert len(parser.toc_links) == 4, parser.toc_links
        assert len(parser.ids) == len(set(parser.ids)), parser.ids
        assert all(link.startswith("#") and link[1:] in parser.ids for link in parser.toc_links), parser.toc_links
        assert "table-of-contents" not in rendered_table, "Headless content has an empty TOC"
        rendered_tasks = (output / "task-fixture/index.html").read_text()
        assert 'id="tasks"' in rendered_tasks, "Disabling TOC must retain heading permalinks"
        assert "table-of-contents" not in rendered_tasks, "toc: false must hide the navigation"
        assert '<input type="checkbox" disabled>' in rendered_tasks, rendered_tasks
        assert '<input type="checkbox" disabled checked>' in rendered_tasks, rendered_tasks
        assert "<strong>docs</strong> &amp; &lt;unsafe&gt;" in rendered_tasks, rendered_tasks
        (output / "keep-on-failure.bin").write_bytes(b"\x00preserve-existing-output\xff")
        protected_tree = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
        for slug in ("search", "archive"):
            collision = project / "content/reserved-fixture.md"
            collision.write_text(f"---\ntitle: Collision\nkind: page\nslug: {slug}\n---\nDo not overwrite generated pages\n")
            for action in ("check", "build"):
                diagnostic = command(str(project / "aja"), action, cwd=project, success=False)
                assert "reserved generated" in diagnostic, diagnostic
                assert (output / "index.html").read_bytes() == original_index, "Route conflict changed output"
                assert {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()} == protected_tree, "Route conflict changed the existing output tree"
            collision.unlink()
        for relative in ("search/index.html", "archive/index.html", "archive/2026/09/index.html", "archive/2026", "search"):
            collision = project / "static" / relative
            assert not collision.exists()
            collision.parent.mkdir(parents=True, exist_ok=True)
            collision.write_text("Do not replace generated discovery output")
            for action in ("check", "build"):
                diagnostic = command(str(project / "aja"), action, cwd=project, success=False)
                assert "reserved generated" in diagnostic, diagnostic
                assert (output / "index.html").read_bytes() == original_index, "Asset conflict changed output"
                assert {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()} == protected_tree, "Asset conflict changed the existing output tree"
            collision.unlink()
            parent = collision.parent
            while parent != project / "static" and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        broken_draft = project / "content/broken-draft.md"
        broken_draft.write_text("---\ntitle: Broken draft\ndate: 2026-10-03\ndraft: true\ntemplate: missing.html\n---\nPreview only\n")
        command(str(project / "aja"), "check", cwd=project)
        draft_check = command(str(project / "aja"), "check", "--drafts", cwd=project, success=False)
        assert "missing template" in draft_check, draft_check
        broken_draft.unlink()
        config_bytes = (project / "aja.json").read_bytes()
        command(str(project / "aja"), "build", "--drafts", cwd=project)
        assert (output / "posts/draft-example/index.html").is_file(), "--drafts must include unpublished content"
        preview_index = json.loads((output / "search.json").read_text())
        assert any(item["url"] == "/posts/draft-example/" for item in preview_index), "Preview search includes drafts"
        assert (project / "aja.json").read_bytes() == config_bytes, "Preview must not persist configuration changes"
        assert not any('/posts/draft-example/' in archive.read_text() for archive in (output / 'archive').rglob('*.html')), "Archive remains published-only during draft preview"
        verify_preview_server(project)
        verify_preview_server(project, flags_first=False)
        command(str(project / "aja"), "build", cwd=project)
        assert not (output / "posts/draft-example").exists(), "Default rebuild must remove preview drafts"
        assert not any(item["url"] == "/posts/draft-example/" for item in json.loads((output / "search.json").read_text()))
        for invalid_args in (("build", "--drats"), ("check", "--drafts", "--drafts"), ("build", "4173"), ("serve", "abc"), ("serve", "0"), ("serve", "65536"), ("serve", "999999999999"), ("serve", "4173", "4174"), ("clean", "--drafts"), ("version", "--drafts"), ("help", "extra")):
            diagnostic = command(str(project / "aja"), *invalid_args, cwd=project, success=False)
            assert "error:" in diagnostic and "\tat " not in diagnostic, diagnostic
            assert (output / "index.html").read_bytes() == original_index, "Invalid arguments changed output"
        (project / "aja.json").write_text('{"title":}', encoding="utf-8")
        for action in ("check", "build", "clean", "serve"):
            diagnostic = command(str(project / "aja"), action, cwd=project, success=False)
            assert "invalid configuration aja.json" in diagnostic, diagnostic
            assert "\tat " not in diagnostic, diagnostic
            assert (output / "index.html").read_bytes() == original_index, "Invalid config changed output"
        (project / "aja.json").write_bytes(config_bytes)
        shutil.rmtree(project / "content")
        (project / "content").mkdir()
        (project / "content/empty-site-page.md").write_text("---\ntitle: Only a page\nkind: page\n---\nSearchable standalone text\n")
        command(str(project / "aja"), "check", cwd=project)
        command(str(project / "aja"), "build", cwd=project)
        assert "No posts yet." in (output / "archive/index.html").read_text()
        assert [path.relative_to(output / "archive").as_posix() for path in (output / "archive").rglob("*.html")] == ["index.html"], "No-post sites must not emit empty month pages"
        assert json.loads((output / "search.json").read_text())[0]["url"] == "/empty-site-page/"
        shutil.rmtree(project / "content")
        (project / "content").mkdir()
        command(str(project / "aja"), "build", cwd=project)
        assert json.loads((output / "search.json").read_text()) == [], "Completely empty sites have a usable empty search index"
    print("Aja integration verification passed")


if __name__ == "__main__":
    main()
