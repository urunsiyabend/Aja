#!/usr/bin/env python3
"""Exercise the real CLI and validate generated artifacts with stdlib only."""
import json
from html.parser import HTMLParser
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
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


def main():
    suite = command(COMPILER, "test")
    assert "Aja tests passed" in suite and "Aja configuration tests passed" in suite, suite
    assert "Table tests passed" in suite, suite
    for marker in ("Heading tests passed", "Metrics tests passed", "Navigation tests passed", "Presentation tests passed", "Task tests passed", "TOC settings tests passed"):
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
        for name in ("index.html", "feed.xml", "sitemap.xml", "robots.txt", "search.json", "about/index.html"):
            assert (output / name).is_file(), name
        for asset in (project / "static").rglob("*"):
            if asset.is_file():
                assert asset.read_bytes() == (output / asset.relative_to(project / "static")).read_bytes(), asset
        assert not (output / "posts/draft-example").exists(), "Draft leaked"
        json.loads((output / "search.json").read_text())
        ET.parse(output / "feed.xml")
        ET.parse(output / "sitemap.xml")
        original_index = (output / "index.html").read_bytes()
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
        (project / "aja.json").write_text('{"title":}', encoding="utf-8")
        for action in ("check", "build", "clean", "serve"):
            diagnostic = command(str(project / "aja"), action, cwd=project, success=False)
            assert "invalid configuration aja.json" in diagnostic, diagnostic
            assert "\tat " not in diagnostic, diagnostic
            assert (output / "index.html").read_bytes() == original_index, "Invalid config changed output"
    print("Aja integration verification passed")


if __name__ == "__main__":
    main()
