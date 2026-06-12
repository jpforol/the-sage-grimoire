# Spec: Section Builder (Capítulos de Prosa)

## Objective
Deterministically build the prose-chapter entries (Criação de Personagens, Regras do
Jogo, Equipamentos) from a reviewed manifest: each section = a page+marker range of the
extracted LivroBasico text, reflowed into Markdown with tables reconstructed.

## Acceptance Criteria
- [ ] `python tools/build_sections.py` reads `tools/data/sections_manifest.json` and
      writes entries to `src/content/codex/<categoria>/` that pass the validator.
- [ ] Each manifest item defines: `title`, `summary`, `category`, start `page` +
      `marker` (heading line); a section ends where the next item starts (or at an
      explicit `end` marker / chapter end).
- [ ] Tables are reconstructed to Markdown:
      - 5-column item tables (`COMUM/INCOMUM/... + PREÇO REQUISITOS DANO TRAÇOS`)
      - 2-column roll tables (`D3/D6/D20 + TÍTULO`), rows re-sorted by roll range
        (the 2-column page layout interleaves them out of order)
- [ ] Prose reflow reuses the ancestry parser conventions (bold leads, `##` headings).
- [ ] Furniture (watermark, page numbers, `Capítulo N`, chapter running headers)
      stripped; report at `.tmp/sections-report.json`; idempotent.

## Edge Cases
- Marker not found on the expected page: search ±1 page, else anomaly + skip section.
- Table rows whose cells wrap across lines: cells joined until the next row key.
- Unrecognized table-ish runs stay as reflowed prose and are flagged for review.

## Links
- Workflow: `workflows/ingest-pdf.md`
- Tool: `tools/build_sections.py`, manifest `tools/data/sections_manifest.json`
- Tests: `tools/tests/test_build_sections.py`
- Related specs: `specs/content-schema.md`, `specs/ancestry-parser.md`
