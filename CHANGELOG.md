# Changelog

All notable changes to Aja are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## 0.2.0 — 2026-10-02

### Changed

- Require and test against the official Siyo v0.7.0 toolchain.
- Handle `std/json`'s `Parsed` / `Invalid` result explicitly instead of
  treating it as a map.
- Export only `ConfigError`, `config.load` and `config.parse` from the
  configuration module using Siyo's `pub` visibility.

### Added

- Markdown task lists with checked/unchecked, disabled accessible checkboxes,
  including ordered lists and safe inline-formatted labels.
- Per-document `toc: false` front matter to hide contents navigation while
  retaining heading permalinks.
- Heading permalinks and an automatic table of contents for content pages.
- Visible-body word counts and estimated reading time, excluding fenced code.
- Previous/next post navigation with deterministic chronological ordering,
  excluding drafts, standalone pages and undated content.
- Default-theme reading aids and corresponding custom-template placeholders.
- Markdown pipe tables with optional outer pipes, left/center/right alignment,
  inline formatting, HTML escaping and deterministic ragged-row handling.
- Typed configuration errors preserve the source path and parser diagnostic;
  CLI commands print a readable error and exit non-zero without a stack trace.
- Configuration regressions and isolated CLI integration verification covering
  generated HTML, JSON/XML, binary-safe assets, drafts and invalid-input safety.
- Release validation before publication, manifest/CLI version consistency
  checks and a SHA-256 checksum file accompanying the source archive.

### Fixed

- Draft-exclusion checks now verify the actual `/posts/draft-example/` output
  path, and nested-source URL documentation matches the generator's flat routes.

### Upgrade notes

- Siyo 0.7.0 is now required; 0.4.0 is no longer the tested toolchain.
- New template placeholders: `toc`, `word_count`, `reading_time`,
  `post_navigation`, `previous_url`, `previous_title`, `next_url`, `next_title`.
- Existing custom templates keep working; add the new placeholders to opt
  into the reading aids. The default theme already includes them.
- CLI integration verification uses Python 3.11+ (standard library only).

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
