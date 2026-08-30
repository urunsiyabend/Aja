---
title: Templates and theming
description: How the template engine, placeholders and the default stylesheet fit together.
date: 2026-08-30
tags: guide, templates, design
---

Aja's template engine is intentionally boring: a template is plain HTML, and
`{{placeholder}}` is replaced with an escaped value. There is no logic, no
loops and no expressions in templates — the Siyo modules do that work.

## The three templates

`templates/base.html` is the document shell: `<head>`, header, footer, and a
single `{{content}}` slot. `post.html` and `page.html` render the body that gets
dropped into that slot. A document can pick a different one with
`template: custom.html` in its front matter.

## Available placeholders

```text
{{site_title}}      site title from aja.json
{{site_tagline}}    tagline shown in the home hero and footer
{{site_author}}     author, used for bylines and <meta name="author">
{{language}}        language attribute for <html lang="...">
{{title}}           document title
{{description}}     document description
{{date}}            publication date
{{tags}}            rendered tag list, linked to tag archives
{{url}}             site-relative URL
{{canonical_url}}   absolute URL built from base_url
{{content}}         rendered body
```

Both `{{key}}` and `{{ key }}` are accepted. Values are HTML-escaped before
substitution, so a title containing `<` cannot break the page.

## Styling

`static/` is copied byte-for-byte into the output, so the default theme is just
`static/style.css`. It ships as a single dependency-free stylesheet that reads
the visitor's `prefers-color-scheme` and adapts, with a readable measure and a
monospace stack for dates and code.

Replace it wholesale and the generator will not notice — Aja emits stable class
names (`hero`, `post-list`, `post-item`, `prose`, `tags`, `pagination`) and
leaves the appearance to you.

## Safety

Template names are validated before they are read: anything containing `..`, `/`
or `\` is rejected, so front matter cannot make the generator load a file from
outside `templates/`.
