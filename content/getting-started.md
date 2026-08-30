---
title: Getting started with Aja
description: Install Siyo, create a site and produce your first build.
date: 2026-08-24
tags: guide, build
---

Aja needs one thing on your machine: the Siyo toolchain. Grab a release from
[SiyoCompiler](https://github.com/urunsiyabend/SiyoCompiler/releases) and make
sure `siyoc` is on your `PATH`.

## Build the site

Clone the repository and run the wrapper script:

```sh
git clone https://github.com/urunsiyabend/Aja.git
cd Aja
./aja build
```

The build prints what it produced and where it went:

```text
Aja focused 4 page(s) and 2 asset(s) in 118ms
Skipped 1 draft(s)
Output: dist/
```

## Preview it

`aja serve` rebuilds the site and then serves `dist/` on the port from
`aja.json`. Each connection is handled by its own actor, so a slow request never
blocks the others.

```sh
./aja serve
# or pick a port
./aja serve 8080
```

## Validate before you publish

`aja check` never writes anything. It loads the configuration, parses every
document, and reports empty titles, posts without dates, missing templates and
duplicate output URLs. It exits non-zero when it finds a problem, which makes it
a good CI gate:

```sh
./aja check && ./aja build
```

## The commands

```text
aja build          generate pages and static artifacts
aja check          validate configuration, metadata, templates and URL clashes
aja serve [port]   rebuild, then serve with concurrent request handling
aja clean          remove the output tree after path safety checks
aja version        print the Aja and Siyo versions
aja help           show command help
```
