#!/usr/bin/env python3
"""Exercise the real CLI and validate generated artifacts with stdlib only."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
COMPILER = shutil.which(os.environ.get("SIYO_BIN", "siyoc"))
if not COMPILER:
    raise SystemExit("Siyo compiler not found; set SIYO_BIN or add siyoc to PATH")
ENV = {**os.environ, "SIYO_BIN": COMPILER}


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
    scratch = os.environ.get("TMPDIR")
    with tempfile.TemporaryDirectory(prefix="aja-verify-", dir=scratch) as directory:
        project = Path(directory) / "site"
        shutil.copytree(ROOT, project, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
        assert "aja 0.1.0 (Siyo 0.7.0)" in command(str(project / "aja"), "version", cwd=project)
        (project / "content/table-fixture.md").write_text(
            "---\ntitle: Table fixture\nkind: page\n---\n"
            "| Name | Value |\n| :--- | ---: |\n| **Aja** | <unsafe> |\n",
            encoding="utf-8",
        )
        command(str(project / "aja"), "check", cwd=project)
        command(str(project / "aja"), "build", cwd=project)
        output = project / "dist"
        for name in ("index.html", "feed.xml", "sitemap.xml", "robots.txt", "search.json", "about/index.html"):
            assert (output / name).is_file(), name
        for asset in (project / "static").rglob("*"):
            if asset.is_file():
                assert asset.read_bytes() == (output / asset.relative_to(project / "static")).read_bytes(), asset
        assert not (output / "notes/draft-example").exists(), "Draft leaked"
        json.loads((output / "search.json").read_text())
        ET.parse(output / "feed.xml")
        ET.parse(output / "sitemap.xml")
        original_index = (output / "index.html").read_bytes()
        rendered_table = (output / "table-fixture/index.html").read_text()
        assert "<table>" in rendered_table and "<strong>Aja</strong>" in rendered_table, rendered_table
        assert "&lt;unsafe&gt;" in rendered_table and "<unsafe>" not in rendered_table, rendered_table
        (project / "aja.json").write_text('{"title":}', encoding="utf-8")
        for action in ("check", "build", "clean", "serve"):
            diagnostic = command(str(project / "aja"), action, cwd=project, success=False)
            assert "invalid configuration aja.json" in diagnostic, diagnostic
            assert "\tat " not in diagnostic, diagnostic
            assert (output / "index.html").read_bytes() == original_index, "Invalid config changed output"
    print("Aja integration verification passed")


if __name__ == "__main__":
    main()
