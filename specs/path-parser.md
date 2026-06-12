# Spec: Path Parser (Trilhas de Especialista e Mestre)

## Objective
Deterministically convert the expert and master path chapters of the LivroBasico
into `trilhas` entries: ~42 especialista paths (p165–198, levels 3/4/6/9) and
~120 mestre paths (p199–278, levels 7/8/10), per the book's Progresso table.

## Acceptance Criteria
- [ ] `python tools/parse_paths.py` reads `.tmp/extracted/livro-basico/` and writes
      entries to `src/content/codex/trilhas/` with `subcategory: especialista|mestre`.
- [ ] Paths are anchored on `<Nome> Nível <N>` header lines; a path needs ≥2 level
      headers (filters false positives from prose).
- [ ] Path section start = last standalone `<Nome>` line before its first level header
      (skips the group index tables), same technique as the spell parser.
- [ ] Entry: intro paragraphs, `## Nível N` sections, auto summary, `source.page`
      (book page of the path heading), tags `[<subcategory>]`.
- [ ] Slug collisions with existing codex entries resolved by `-trilha` suffix.
- [ ] Group headings/index tables (`Trilhas da Batalha`…) are not emitted as paths;
      skipped content is counted in the report.
- [ ] Output passes `tools/validate_entries.py`; report at `.tmp/path-parse-report.json`;
      idempotent.

## Edge Cases
- Page ranges: especialista = file pages 166–199, mestre = 200–279 (file page N =
  book page N−1).
- A few paths share names with spells or other entries → suffix rule keeps slugs unique.
- Wrapped/odd headers that yield a single level header → anomaly, not an entry.

## Links
- Workflow: `workflows/ingest-pdf.md`
- Tool: `tools/parse_paths.py` (reuses `reflow`/`first_sentence` from
  `tools/parse_ancestries.py` and `slugify` from `tools/validate_entries.py`)
- Tests: `tools/tests/test_parse_paths.py`
- Related specs: `specs/content-schema.md`, `specs/spell-parser.md`,
  `specs/ancestry-parser.md`
