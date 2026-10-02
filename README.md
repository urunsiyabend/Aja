# Aja

Aja is a static site generator written entirely in [Siyo](https://github.com/urunsiyabend/SiyoCompiler).
It reads Markdown from `content/`, applies HTML templates from `templates/`,
copies `static/` byte-for-byte and writes a deployable site into `dist/`.

There are no runtime dependencies beyond the Siyo standard library — the
Markdown renderer, the front matter parser, the template engine, the feed
writers and the development server are all part of this project.

The name comes from JoJo's **Red Stone of Aja**: content, templates and assets
arrive from different directions, and Aja focuses them into a single output.

## Requirements

- [Siyo 0.7.0](https://github.com/urunsiyabend/SiyoCompiler/releases) (the tested toolchain)
- `siyoc` on your `PATH`

## Quick start

```sh
git clone https://github.com/urunsiyabend/Aja.git
cd Aja
./aja check
./aja build
./aja serve
```

Then open <http://localhost:4173>. The generated site lands in `dist/`.

On Windows, or without the wrapper script, call the compiler directly:

```sh
siyoc run build
siyoc run serve 8080
```

## Commands

```text
aja build          generate pages and static artifacts
aja check          validate configuration, metadata, templates and URL clashes
aja serve [port]   rebuild, then serve files with concurrent request handling
aja clean          remove the output tree after applying path safety checks
aja version        print the Aja and Siyo versions
aja help           show command help
```

`aja check` writes nothing and exits non-zero on the first problem it finds,
which makes `./aja check && ./aja build` a usable CI gate.

## Features

- Recursive Markdown discovery with YAML-style front matter
- Posts, pages and drafts, with per-document template selection
- Headings, paragraphs, lists, blockquotes, horizontal rules, fenced code and
  inline Markdown
- Pipe tables with column alignment and escaped, inline-formatted cells
- HTML escaping everywhere, plus link-scheme filtering
- Paginated post indexes and generated tag archives
- RSS 2.0, XML sitemap, `robots.txt` and a JSON search index
- Recursive, binary-safe static asset copying
- A concurrent development server with canonical-path traversal protection
- Strict JSON configuration parsing with typed errors and readable CLI diagnostics

## Writing content

Every file under `content/` is Markdown with a front matter block:

```md
---
title: Focused light
description: A short summary used in listings and feeds.
date: 2026-08-30
tags: siyo, compiler
draft: false
---

# A real heading

Body written in **Markdown**.
```

Supported keys are `title`, `description`, `date`, `tags`, `draft`, `kind`,
`slug`, `weight` and `template`. Set `kind: page` for a standalone page; any
other document is a post. `content/notes/deep-dive.md` becomes
`/notes/deep-dive/`; `slug` overrides the last segment.

### Markdown tables

```md
| Feature | Status |
| :--- | ---: |
| **Tables** | Supported |
| Typed configuration errors | Supported |
```

Outer pipes are optional. `:---`, `:---:` and `---:` align a column left,
center and right. Separators need at least three hyphens per column. Short
rows are padded with empty cells; extra cells are discarded. This is a small
pipe-table subset: literal/escaped pipes in cells and multiline cells are not
supported.

## Templates

Templates are plain HTML with `{{placeholder}}` substitution — no logic, no
loops. `base.html` is the document shell and holds the single `{{content}}`
slot; `post.html` and `page.html` render the body dropped into it.

```text
{{site_title}}   {{site_tagline}}   {{site_author}}   {{language}}
{{title}}        {{description}}    {{date}}          {{tags}}
{{url}}          {{canonical_url}}  {{content}}
```

Both `{{key}}` and `{{ key }}` are accepted, and every value is HTML-escaped
before substitution. Template names containing `..`, `/` or `\` are rejected, so
front matter cannot load a file from outside `templates/`.

## Configuration

`aja.json` holds site identity, input/output directories, pagination, draft
policy and the development server port.

```json
{
  "title": "Aja",
  "tagline": "A static site generator written in Siyo.",
  "description": "Aja turns Markdown, templates and static assets into a deployable static site.",
  "author": "Siyabend Ürün",
  "language": "en",
  "base_url": "http://localhost:4173",
  "content_dir": "content",
  "templates_dir": "templates",
  "static_dir": "static",
  "output_dir": "dist",
  "posts_per_page": 5,
  "include_drafts": false,
  "port": 4173
}
```

## Layout

```text
content/     Markdown sources
templates/   base, post and page templates
static/      files copied byte-for-byte into the output
src/         Aja's Siyo modules and its test suite
dist/        generated output, ignored by Git
aja.json     site configuration
siyo.toml    Siyo project manifest
```

## Development

```sh
siyoc test       # run the Siyo test suite in src/test.siyo
./aja check      # validate the example site
./aja build      # regenerate dist/
python3 scripts/verify.py  # isolated CLI and generated-artifact verification
```

The default theme is a single dependency-free stylesheet in
`static/style.css`. It follows the visitor's `prefers-color-scheme` and styles
the stable class names Aja emits (`hero`, `section-title`, `post-list`,
`post-item`, `prose`, `tags`, `pagination`). Replace it wholesale and the
generator will not notice.

## Known limitations

The official Siyo v0.7.0 Linux archive currently reports `siyoc 0.6.0` from
`--version`. CI pins the v0.7.0 release archive; Aja's requirements refer to
that release, not the stale version banner. Use `siyoc test` / `siyoc run`;
the release's interpreter has a typed-error payload incompatibility.

- The Markdown subset is deliberately small: no footnotes or reference
  links.
- Templates have no conditionals or loops; anything dynamic belongs in `src/`.
- The development server is for local previews, not production hosting.

## License

MIT. See [LICENSE](LICENSE).
