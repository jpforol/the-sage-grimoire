# Spec: Ancestry Parser (Ancestralidades + Trilhas de Ancestralidade)

## Objective
Deterministically convert the 30 two-page ancestry spreads of
`SOTWW-Ancestralidades.pdf` into 60 codex entries: one `ancestralidades` entry
(lore + traços) and one `trilhas` entry with `subcategory: ancestralidade`
(the "X de Nível 1/2/5" sections) per ancestry. Humana (LivroBasico p11) is
AI-structured separately — it has no spread in the supplement.

## Acceptance Criteria
- [ ] `python tools/parse_ancestries.py` reads `.tmp/extracted/ancestralidades/` and
      writes 60 entries (30 + 30) that pass `tools/validate_entries.py`.
- [ ] Ancestries are discovered from the `Traços de <X>` marker lines (30 found);
      each spread = the marker's page file and the one before it.
- [ ] Ancestry entry: lore paragraphs (with detected section headings), `## Traços`
      section, and stats parsed from the traços header (`vida`, `tamanho`,
      `velocidade`, `sentidos`, `idiomas_bonus` when present).
- [ ] Trilha entry: title `Trilha de <X>`, slug `trilha-de-<x>` (avoids collision with
      the ancestry slug), `subcategory: ancestralidade`, body split into
      `## Nível 1/2/5` sections.
- [ ] `source.page` uses book page numbers (file page-NNN = book page NNN−1).
- [ ] Watermark/furniture lines stripped (as in the spell parser).
- [ ] Anomaly report at `.tmp/ancestry-parse-report.json`; idempotent re-runs.

## Edge Cases
- Trait/name paragraphs (`Alvo Difícil: …`) are re-flowed: a new paragraph starts at
  `Nome: ` patterns, rendered as `**Nome:** …`.
- Lore headings (`Aventureiros Anões`) detected as short Title-Case lines without
  terminal punctuation → `##` headings; misdetection falls back to body text (logged).
- ALL-CAPS label lines (`NOMES COMUNS DE ANÃO:`) become bold paragraph leads.
- Missing `X de Nível 1` marker: trilha entry skipped, anomaly logged.

## Links
- Workflow: `workflows/ingest-pdf.md`
- Tool: `tools/parse_ancestries.py`
- Tests: `tools/tests/test_parse_ancestries.py`
- Related specs: `specs/content-schema.md`, `specs/pdf-extraction-pipeline.md`,
  `specs/spell-parser.md` (same furniture conventions)
