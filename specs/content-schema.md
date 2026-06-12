# Spec: Content Schema (Codex Entries)

## Objective
Define the single contract every codex entry follows, so the site (Astro/Zod), the
validation tool (Python), and AI-assisted PDF structuring all agree on what a valid
entry is. One schema, enforced twice: at build time by `src/content.config.ts` (Zod)
and pre-commit/CI by `tools/validate_entries.py`.

## Acceptance Criteria
- [ ] Every entry is a Markdown file at `src/content/codex/<categoria>/<slug>.md`.
- [ ] Frontmatter validates against the contract below (both Zod and Python validator).
- [ ] Slugs are unique across the whole collection.
- [ ] `tools/validate_entries.py` exits 0 on a valid tree, 1 with clear messages on violations.
- [ ] Adding a new category requires only: extend the enum here, add a registry entry
      in `src/data/categories.ts`, and mirror the enum in the validator.

## Frontmatter Contract

```yaml
---
title: "Bola de Fogo"            # required, non-empty string
category: "magias"               # required, enum (see below); must match parent folder
summary: "Uma explosão de chamas que devasta uma área."  # required, shown in listings
tags: ["fogo", "evocação"]       # optional, lowercase strings; drives filters
stats:                           # optional map of category-specific fields,
  circulo: 3                     # rendered in order as a stat block
  alcance: "30 metros"
source:                          # optional but expected for PDF-derived entries
  book: "livro-do-jogador"       # slug of the source PDF
  page: 142                      # positive integer
draft: false                     # optional, default false; true = hidden everywhere
---
Corpo da entrada em Markdown (descrição completa, tabelas, listas...).
```

### Category enum (v1)
`classes` | `magias` | `itens` | `regras`

Extensible: new categories are added to this spec first, then to
`src/data/categories.ts` and `tools/validate_entries.py`.

### Slug rules
- Derived from the title: ASCII-fold accents (`ç`→`c`, `ã`→`a`, `é`→`e`...),
  lowercase, non-alphanumerics collapsed to single hyphens, trimmed.
  Example: `"Coração de Dragão"` → `coracao-de-dragao`.
- The slug is the filename (without `.md`); uniqueness is global across categories
  (avoids search/anchor collisions).

## Inputs / Outputs

### Inputs
- Entry `.md` files under `src/content/codex/`.

### Outputs
- Validation verdict (exit code + per-file error messages from the Python tool;
  build failure with Zod messages from Astro).

## Edge Cases
- `category` doesn't match the parent folder name: validation error.
- Duplicate slug in different categories: validation error (global uniqueness).
- Tags with uppercase or accents: validation error with the normalized suggestion.
- Empty `title`/`summary`: validation error.
- Unknown top-level frontmatter keys: validation error (catches typos like `sumary`).
- `stats` values: scalars (string/number/boolean) only — nested objects rejected.

## Links
- Tool: `tools/validate_entries.py`, `tools/new_entry.py`
- Tests: `tools/tests/test_validate_entries.py`
- Related specs: `specs/codex-site.md` (consumer), `specs/pdf-extraction-pipeline.md` (producer)
- Site enforcement: `src/content.config.ts`
