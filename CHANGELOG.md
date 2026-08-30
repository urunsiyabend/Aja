# Changelog

All notable changes to Aja are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.0 — 2026-08-30

First release. Aja is a static site generator written entirely in Siyo,
requiring Siyo 0.4.0 or newer.

### Content

- Recursive Markdown discovery under `content/`, with nested directories
  mapped onto the output URL structure
- YAML-style front matter: `title`, `description`, `date`, `tags`, `draft`,
  `kind`, `slug`, `weight` and `template`
- Markdown rendering for headings, paragraphs, lists, blockquotes, horizontal
  rules and fenced code blocks, plus inline code, bold, italic and links
- HTML escaping on every output path, and link-scheme filtering that
  neutralises anything other than `http`, `https` and `mailto`

### Output

- Post and page rendering through `base.html` plus a per-document template
- Paginated post indexes and generated tag archive pages
- RSS 2.0 feed, XML sitemap, `robots.txt` and a JSON search index
- Recursive, binary-safe static asset copying

### Tooling

- `aja build`, `check`, `serve`, `clean`, `version` and `help`
- `aja check` validates configuration, front matter, template existence and
  duplicate output URLs without writing anything, and exits non-zero on failure
- Development server that handles each connection in its own actor, with
  canonical-path traversal protection
- `aja clean` refuses to delete unsafe output directories
- Siyo test suite in `src/test.siyo`

### Theme

- Dependency-free default stylesheet that follows `prefers-color-scheme`
