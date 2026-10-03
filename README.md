# Aja

Version **0.3.0** — requires **Siyo 0.7.0**.

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
aja build [--drafts]          generate pages and static artifacts
aja check [--drafts]          validate config, templates and URL clashes
aja serve [port] [--drafts]   rebuild, then serve concurrent requests
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
- Markdown task lists with read-only checked/unchecked checkboxes
- HTML escaping everywhere, plus link-scheme filtering
- Paginated post indexes and generated tag archives
- RSS 2.0, XML sitemap, `robots.txt` and a full-text JSON search index
- Accessible client-side search at `/search/`, with accent-insensitive matching
- Monthly published-post archives at `/archive/` and `/archive/YYYY/MM/`
- Explicit `--drafts` previews without changing site configuration
- Recursive, binary-safe static asset copying
- A concurrent development server with canonical-path traversal protection
- Strict JSON configuration parsing with typed errors and readable CLI diagnostics
- Stable heading permalinks and automatically generated table of contents
- Word counts and estimated reading time in the default theme
- Previous/next post links ordered chronologically, independent of listing weight

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
`slug`, `weight`, `template` and `toc`. Set `kind: page` for a standalone page; any
other document is a post. `content/notes/deep-dive.md` becomes
`/posts/deep-dive/` as a post, or `/deep-dive/` with `kind: page`;
`slug` overrides the document's last segment. Discovery is recursive, but
parent directory names are not included in the output URL.

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

### Task lists

```md
- [ ] Write documentation
- [x] Run tests
1. [X] Verify the release
```

Task lists work in ordered and unordered lists. Labels keep inline Markdown
formatting and HTML escaping; fenced code remains untouched. Checkboxes are
disabled, static indicators, not an interactive task-storage feature.

## Templates

Templates are plain HTML with `{{placeholder}}` substitution — no logic, no
loops. `base.html` is the document shell and holds the single `{{content}}`
slot; `post.html` and `page.html` render the body dropped into it.

```text
{{site_title}}   {{site_tagline}}   {{site_author}}   {{language}}
{{title}}        {{description}}    {{date}}          {{tags}}
{{url}}          {{canonical_url}}  {{content}}
{{toc}}          {{word_count}}     {{reading_time}}
{{post_navigation}}
{{previous_url}} {{previous_title}} {{next_url}} {{next_title}}
```

Both `{{key}}` and `{{ key }}` are accepted. Scalar text values are escaped
before substitution; `content`, `tags`, `toc` and `post_navigation` contain
HTML generated by Aja. Template names containing `..`, `/` or `\` are rejected, so
front matter cannot load a file from outside `templates/`.

## Reading aids

The default post and page templates include `{{toc}}`. It is empty when the
body has no headings; otherwise it links to the body heading permalinks.
Duplicate heading IDs are disambiguated, and code-block headings do not enter
the contents list. To hide the contents list in a custom theme, omit `{{toc}}`.
For a single document, set `toc: false` (or `toc: no`) in its front matter;
heading permalinks remain available. The default is enabled.

`{{word_count}}` counts visible body words, not HTML attributes or fenced code.
Inline code and heading text are included. `{{reading_time}}` is an estimate in
whole minutes: 200 words per minute, rounded up (zero for an empty body).

`{{post_navigation}}` renders only available previous/next links. Previous
means an older post and next means a newer one, using ascending `YYYY-MM-DD`
dates and URL as the tie-breaker. Drafts, standalone pages and undated posts
are excluded. This order does not alter weighted homepage listings.

## Search and archives

`/search/` searches titles, descriptions, tags and rendered body text, including
code examples. Every query term must match; title matches rank ahead of metadata
and body-only matches. Matching ignores accents, NFC/NFD differences and Turkish
`İ`/`I`/`i`/`ı` distinctions. Results use safe DOM text rather than injected HTML.
Share a query using `/search/?q=your+query`; live input updates that URL.

Search uses the dependency-free `static/search.js` and requires JavaScript in
the visitor’s browser. Custom themes still receive `/search/`; retain/copy
`static/search.js` into a custom `static_dir`. The JSON array keeps its existing
metadata fields and adds `content` containing decoded rendered body text.

`/archive/` links to monthly archives with post counts. Months and posts are
newest first, independent of homepage `weight`; equal-date posts use URL order.
Only published posts with valid Gregorian `YYYY-MM-DD` dates participate; drafts
and standalone pages do not, even in draft preview. No-post sites get a readable
empty archive without empty month pages. Discovery pages enter the sitemap.

The generated `/search/` and `/archive/` routes are reserved. Rename standalone
pages that used these slugs. Conflicting static files at generated discovery
paths (or file ancestors blocking them) fail `check` and `build` before the
existing output is deleted. Add Search and Archive links to custom navigation
to expose the new pages; the bundled theme includes them.

## Draft previews

```sh
./aja check --drafts
./aja build --drafts
./aja serve 4173 --drafts  # --drafts may also precede the port
```

The flag enables draft content for that invocation only and never rewrites
`aja.json`. Preview output—including the homepage, search index, feed and
sitemap—can contain drafts: **do not deploy it**. Run a normal build again with
`include_drafts: false` to remove them. Archive pages stay published-only.
Unknown/duplicate options, extra arguments and invalid CLI ports fail rather
than being silently ignored. Ports must be decimal values from 1 to 65535.

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

The CLI/artifact verification script requires Python 3.11+ and uses only the
standard library. JavaScript search unit tests use Node.js 22 (also pinned in
CI); Node is a development-only dependency, not needed to generate or serve
your site. Aja itself still needs only the Siyo runtime.

```sh
siyoc test       # run the Siyo test suite in src/test.siyo
./aja check      # validate the example site
./aja build      # regenerate dist/
python3 scripts/verify.py  # isolated CLI, artifacts and draft-server verification
node scripts/search_test.mjs  # browser-search logic and safe URL regressions
```

The default theme uses a dependency-free search script (`static/search.js`) and
stylesheet (`static/style.css`). The stylesheet follows the visitor's
`prefers-color-scheme` and styles
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
