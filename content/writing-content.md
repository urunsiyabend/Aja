---
title: Writing content
description: Front matter keys, the supported Markdown subset and how URLs are derived.
date: 2026-08-27
tags: guide, markdown, content
---

Every document under `content/` is a Markdown file with a front matter block
delimited by `---`. Directories nest freely; the path becomes part of the URL.

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

## Front matter keys

- `title` — document title, required by `aja check`
- `description` — summary for listings, `<meta>` tags, RSS and the search index
- `date` — publication date, required for posts
- `tags` — comma-separated list; each tag gets an archive page
- `draft` — `true` keeps the document out of production builds
- `kind` — `page` for a standalone page; anything else is a post
- `slug` — overrides the URL segment derived from the filename
- `weight` — sort hint for pages
- `template` — template file to render with, default `post.html` or `page.html`

## URLs

`content/notes/deep-dive.md` becomes `/notes/deep-dive/`, written to
`dist/notes/deep-dive/index.html`. Set `slug` to override the last segment.
`aja check` fails the build if two documents resolve to the same URL.

## Supported Markdown

Aja implements a deliberately small subset, rendered by its own parser:

- ATX headings, paragraphs and horizontal rules
- Ordered and unordered lists
- Blockquotes
- Fenced code blocks
- Inline `code`, **bold**, *italic* and [links](https://github.com/urunsiyabend/Aja)

> Everything is escaped on the way out. Fenced code is escaped as text, and
> links with schemes other than `http`, `https` and `mailto` are neutralised.

Code fences keep their language hint so a highlighter can pick it up later:

```siyo
fn focus(input: string) -> string {
    "Aja: " + input
}
```

## Drafts

A document with `draft: true` is skipped and counted in the build summary. Set
`include_drafts` to `true` in `aja.json` to render them locally.
