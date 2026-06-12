# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

**The Sage Grimoire** — a static, PT-BR codex website (Archives of Nethys style) for a
personal RPG system, deployed free on GitHub Pages at
`https://jpforol.github.io/the-sage-grimoire/`. Content will be ingested from 3 source
PDFs (dropped into `sources/`, gitignored) via the pipeline in
`workflows/ingest-pdf.md`. Current entries under `src/content/codex/` are samples that
define the reference format.

## Methodology

This project follows **Spec-Driven Development (SDD) + WAT**, inherited from the global
`~/.claude/CLAUDE.md`. The short version, applied here:

- **Specs are the source of truth.** Before writing or changing code, write or update
  the spec in `specs/<feature>.md`. If a bug traces back to an incomplete spec, fix the
  spec first.
- **Reasoning vs. execution split.** Keep AI work at the reasoning (agent) and design
  (spec) layers. Push deterministic execution down into testable Python tools in
  `tools/` so chained steps stay reliable.
- **Look for an existing tool before writing a new one.** Check `tools/` against what
  the spec requires; only create a new script when nothing fits.
- **Evolve specs and code together.** When you hit an edge case or constraint, capture
  it in the spec/workflow so the next run benefits.

## Repository Layout

```
specs/       # One structured Markdown spec per feature (template in global CLAUDE.md)
workflows/   # WAT SOPs, generated from specs and kept in sync
tools/       # Deterministic Python scripts — the execution layer
sources/     # The 3 source PDFs (gitignored; never committed)
src/         # Astro site: content collection, components, pages, theme
.tmp/        # Disposable intermediates (safe to delete/regenerate)
```

A spec's `## Links` section is the map between intent and implementation — it points to
the workflow(s), tool(s), and tests that fulfill it. Read the spec first, then follow
its links.

## Commands

```sh
npm install                  # site dependencies (Astro + Pagefind)
npm run dev                  # dev server at http://localhost:4321/the-sage-grimoire/
npm run build                # astro build + pagefind index over dist/
npm run preview              # serve dist/ — the ONLY place search works locally

# Python tools (venv at .venv/)
pip install -r tools/requirements.txt
python tools/validate_entries.py src/content/codex/    # content gate (CI runs this too)
python tools/new_entry.py magias "Nome" --tags a,b     # scaffold a valid entry
python tools/extract_pdf.py sources/X.pdf --out .tmp/extracted/X/

pytest tools/tests/                                    # full tool test suite
pytest tools/tests/test_validate_entries.py -k slug    # single test
```

Push to `main` → `.github/workflows/deploy.yml` validates entries, builds, and deploys
to GitHub Pages.

## Architecture

The chain for all content: **PDF → `tools/extract_pdf.py` (deterministic text) →
AI-assisted structuring per `workflows/ingest-pdf.md` → Markdown entries in
`src/content/codex/<categoria>/<slug>.md` → Astro build → static site + Pagefind
index.**

- **One schema, enforced twice**: `specs/content-schema.md` is the contract; it is
  executable as Zod in `src/content.config.ts` (build-time) and as
  `tools/validate_entries.py` (pre-commit/CI). Change one → change all three.
- **Category registry**: `src/data/categories.ts` drives nav, home cards, and routes
  (`src/pages/[category]/`). Adding a category touches: schema spec → registry →
  Zod enum → Python validator.
- **Base path is load-bearing**: the site deploys to a subpath, so every internal
  link goes through `url()` from `src/utils/url.ts`. Never hardcode root-relative
  URLs (see specs/codex-site.md).
- **Search**: Pagefind indexes `dist/` post-build (`data-pagefind-body` marks entry
  pages). It does not work in `npm run dev` by design.
