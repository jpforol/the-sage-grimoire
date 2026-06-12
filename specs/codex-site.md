# Spec: Codex Site (The Sage Grimoire)

## Objective
A static, free-to-host web codex (in Português BR) for the group's RPG system, modeled
on https://2e.aonprd.com/: friends browse categories (classes, magias, itens, regras),
open entry pages with stat blocks, filter listings by tags, and use instant full-text
search. Content originates from 3 source PDFs (see `specs/pdf-extraction-pipeline.md`);
the site itself is content-agnostic and renders whatever valid entries exist in
`src/content/codex/`.

Hosted on GitHub Pages under a subpath: `https://<user>.github.io/the-sage-grimoire/`.

## Acceptance Criteria
- [ ] Home page shows a search box and a grid of category cards (label, icon, count).
- [ ] Each category has a listing page at `/<categoria>/` with all its entries and
      client-side tag filtering (instant show/hide, no reload).
- [ ] Each entry has a page at `/<categoria>/<slug>/` rendering: title, summary,
      styled stat block (from `stats`), Markdown body, tags, and source (book + page).
- [ ] Pagefind search works on the deployed site, including accented Portuguese terms.
- [ ] All internal links and assets work under the GitHub Pages subpath.
- [ ] Responsive: usable on mobile (friends will consult mid-session on phones).
- [ ] Dark grimoire theme: dark background, gold/amber accents, serif display fonts.
- [ ] UI text is entirely in Português (BR); `<html lang="pt-BR">`.

## Inputs / Outputs

### Inputs
- Entry Markdown files in `src/content/codex/<categoria>/<slug>.md` conforming to
  `specs/content-schema.md`.
- Category registry in `src/data/categories.ts`.

### Outputs
- Static site in `dist/` (Astro build + Pagefind index), deployed to GitHub Pages.

## Edge Cases
- Entry with empty/missing `stats`: entry page renders without a stat block (no empty box).
- Category with zero entries: listing page shows a friendly "Nenhuma entrada ainda" message.
- Accents/ç in titles: slugs are ASCII-folded (see content-schema spec); search still
  matches accented queries (Pagefind handles diacritics).
- Search in dev mode: Pagefind only indexes `dist/`, so search works only after
  `npm run build` (use `npm run preview`). This is expected, not a bug.
- Draft entries (`draft: true`): excluded from listings, pages, and the search index.

## Conventions
- **Base path**: every internal link/asset MUST use `import.meta.env.BASE_URL` (or
  Astro helpers that respect `base`). Hardcoded root-relative URLs (`/magias/`) break
  on GitHub Pages subpaths. This is the #1 failure mode — check it in review.

## Links
- Workflow: `workflows/ingest-pdf.md` (how content gets into the site)
- Tool: `tools/validate_entries.py` (content gate), `tools/new_entry.py` (scaffold)
- Tests: `npm run build` (type-checked schema via Zod) + visual verification
- Related specs: `specs/content-schema.md`, `specs/pdf-extraction-pipeline.md`
