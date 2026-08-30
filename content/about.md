---
kind: page
title: About
description: What Aja is and why it exists.
weight: 10
---

Aja is a static site generator written entirely in [Siyo](https://github.com/urunsiyabend/SiyoCompiler).
It reads Markdown from `content/`, applies HTML templates from `templates/`,
copies `static/` byte-for-byte and writes a deployable site into `dist/`.

The whole generator is about 1,100 lines of Siyo across thirteen modules — the
Markdown renderer, the front matter parser, the template engine, the feed
writers and the development server are all part of the project. There are no
runtime dependencies beyond the Siyo standard library.

## What it does

- Recursive Markdown discovery with YAML-style front matter
- Posts, pages and drafts, with per-document template selection
- Paginated post indexes and generated tag archives
- RSS 2.0, XML sitemap, `robots.txt` and a JSON search index
- Byte-safe static asset copying
- A concurrent development server with path-traversal protection

## The name

Aja is named after the Red Stone of Aja: content, templates and assets arrive
from different directions, and the generator focuses them into a single output.
