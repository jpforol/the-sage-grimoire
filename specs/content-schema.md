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
title: "Chamas Reluzentes"       # required, non-empty string
category: "magias"               # required, enum (see below); must match parent folder
subcategory: "novato"            # optional; only allowed where the category defines it
summary: "Fogo arcano que salta entre inimigos."  # required, shown in listings
tags: ["pirosofia", "ataque"]    # optional, lowercase strings; drives filters
stats:                           # optional map of category-specific fields,
  tradicao: "Pirosofia"          # rendered in order as a stat block
  conjuracoes: 1
  alvo: "Uma criatura a até 10 metros"
  duracao: "Instantânea"
source:                          # required for PDF-derived entries (traceability)
  book: "livro-basico"           # livro-basico | ancestralidades
  page: 142                      # positive integer (book page number)
draft: false                     # optional, default false; true = hidden everywhere
---
Corpo da entrada em Markdown (descrição completa, tabelas, listas...).
```

### Category enum (v2 — Shadow of the Weird Wizard)
`criacao-de-personagens` | `regras` | `equipamentos` | `magias` | `ancestralidades` | `trilhas`

| Category | Content | Source |
| --- | --- | --- |
| `criacao-de-personagens` | Guia de criação, seções do cap. 1 | livro-basico p10–26 |
| `regras` | Regras principais do jogo | livro-basico p27–54 |
| `equipamentos` | Equipamentos básicos | livro-basico p55–75 |
| `magias` | Um feitiço por entrada + intro por tradição | livro-basico p76–164 |
| `ancestralidades` | Uma entrada por ancestralidade | ancestralidades (Humana: livro-basico p11) |
| `trilhas` | Uma entrada por trilha, com `subcategory` | ver abaixo |

### Subcategory (per-category enum)
Only `trilhas` defines subcategories; any other category with `subcategory` is a
validation error.

- `trilhas`: `novato` (livro-basico p21–25) | `ancestralidade` (ancestralidades) |
  `especialista` (livro-basico p165–198) | `mestre` (livro-basico p199–278).
  Trilhas entries MUST have a subcategory. Rules prose (shared novato/ancestralidade
  levels; Humana restricted to novato) lives in the trilhas listing page intro.

### Magias stats conventions
Spell entries use these `stats` keys when present in the book, in this order:
`tradicao`, `conjuracoes`, `requisito`, `alvo`, `area`, `duracao`, `disparo`.
Tags: the tradition slug (e.g. `pirosofia`) plus optional functional tags.
Tradition intro entries (the chapter text that opens each tradition) use the slug
pattern `tradicao-<slug>` and tag `tradicao`.

Extensible: new categories/subcategories are added to this spec first, then to
`src/data/categories.ts`, `src/content.config.ts` and `tools/validate_entries.py`.

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
- `subcategory` on a category that doesn't define one: validation error.
- `trilhas` entry without `subcategory` or with value outside the enum: validation error.
- `source.book` outside `livro-basico` | `ancestralidades`: validation error.

## Links
- Tool: `tools/validate_entries.py`, `tools/new_entry.py`
- Tests: `tools/tests/test_validate_entries.py`
- Related specs: `specs/codex-site.md` (consumer), `specs/pdf-extraction-pipeline.md` (producer)
- Site enforcement: `src/content.config.ts`
