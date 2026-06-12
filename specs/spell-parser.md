# Spec: Spell Parser (Magias)

## Objective
Deterministically convert the extracted text of LivroBasico p76–164 into one valid
codex entry per spell (~594) plus one intro entry per tradition (~33), eliminating
hand-structuring of the largest chapter. AI/human only reviews the anomaly report.

## Acceptance Criteria
- [ ] `python tools/parse_spells.py` reads `.tmp/extracted/livro-basico/page-{076..164}.txt`
      and writes entries to `src/content/codex/magias/`.
- [ ] Each spell entry has: title (PT title-case from the ALL-CAPS name), stats
      (`tradicao`, `rank`, `conjuracoes`, `alvo`, `duracao`), tags (tradition slug +
      rank), `source.page` (book page where the spell name appears), auto summary
      (first sentence of body).
- [ ] Each tradition gets an intro entry `tradicao-<slug>.md` (tag `tradicao`) with the
      text between the tradition heading and its first spell.
- [ ] All output passes `tools/validate_entries.py` (slug rules, schema).
- [ ] Slug collisions between spells of different traditions are resolved by appending
      the tradition slug.
- [ ] Watermark lines (`Licenciado para ...`), page numbers and `Capítulo N` furniture
      are stripped — personal data never reaches the site.
- [ ] `.tmp/spell-parse-report.json` lists: counts per tradition/rank, and anomalies
      (spell with empty body, unparsed text chunks, suspicious lengths) for review.
- [ ] Idempotent: re-running regenerates the same files.

## Parsing model
1. Tradition names are derived from the 66 rank headers (`Especialista|Mestre +
   de/da/das/do/dos + Nome`); the start of each tradition section is the standalone
   title-case line equal to the name. Rank state machine per tradition:
   iniciado → (header) especialista → (header) mestre.
2. A spell starts at an ALL-CAPS line whose following lines contain `CONJURAÇÕES:`;
   stat lines (`CONJURAÇÕES`, `ALVO`, `DURAÇÃO`) are consumed; the body runs until the
   next spell name, rank header, or tradition heading.

## Inputs / Outputs
### Inputs
- `.tmp/extracted/livro-basico/page-076.txt` … `page-164.txt` (from `tools/extract_pdf.py`).
### Outputs
- `src/content/codex/magias/<slug>.md` (~594 spells + ~33 tradition intros).
- `.tmp/spell-parse-report.json` (anomaly report).

## Edge Cases
- Sidebar boxes (e.g. `FEITIÇOS DE EVOCAÇÃO:`) — ALL-CAPS lines with `:` that are not
  followed by `CONJURAÇÕES:` are not spells; their text is flagged in the report if it
  lands inside a spell body.
- Same spell name in two traditions: slug suffixing keeps global uniqueness.
- In-spell tables (d6 rolls): kept as plain text lines; spells with table-like lines
  are flagged for optional manual Markdown-table cleanup.
- A spell whose body crosses a page break: body continues across page files; the
  `source.page` is the page of the name line.

## Links
- Workflow: `workflows/ingest-pdf.md`
- Tool: `tools/parse_spells.py`
- Tests: `tools/tests/test_parse_spells.py`
- Related specs: `specs/content-schema.md` (target format),
  `specs/pdf-extraction-pipeline.md` (input)
