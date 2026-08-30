---
title: A draft that stays unpublished
description: Demonstrates how drafts are skipped in production builds.
date: 2026-09-02
tags: draft
draft: true
---

This document has `draft: true`, so a normal `aja build` skips it and reports it
in the "Skipped N draft(s)" line.

Set `include_drafts` to `true` in `aja.json` to render drafts while you work on
them locally.
