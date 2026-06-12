# Spec: PDF Extraction Pipeline

## Objective
Turn the 3 source rulebook PDFs into raw, reviewable text so entries can be structured
into the codex. The deterministic half (PDF → ordered text per page + manifest) lives
in a Python tool; the interpretive half (raw text → structured entry files) is
AI-assisted and human-reviewed, governed by `workflows/ingest-pdf.md`. The split keeps
the unreliable part (layout interpretation) inspectable and the repeatable part scripted.

## Acceptance Criteria
- [ ] `python tools/extract_pdf.py sources/<book>.pdf --out .tmp/extracted/<book>/`
      produces one `page-NNN.txt` per page plus `manifest.json`.
- [ ] Text blocks are emitted in reading order (top-to-bottom, left-column-first for
      multi-column pages).
- [ ] Hyphenated line-break words are rejoined (`fei-\ntiço` → `feitiço`).
- [ ] `manifest.json` lists: page count, per-page block counts, and pages flagged as
      suspect (very low text yield, heavy block overlap — likely tables/images).
- [ ] Encrypted or image-only (scanned) PDFs fail fast with a clear Portuguese-friendly
      error message; OCR is explicitly out of scope for v1.
- [ ] Tool is idempotent: re-running overwrites the output directory deterministically.

## Inputs / Outputs

### Inputs
- A PDF file in `sources/` (gitignored; the 3 rulebooks are dropped there by the owner).

### Outputs
- `.tmp/extracted/<book>/page-001.txt` ... `page-NNN.txt` — plain text per page.
- `.tmp/extracted/<book>/manifest.json` — extraction metadata + suspect-page flags.

## Edge Cases
- Multi-column layout: blocks sorted by column detection (x-position clustering) then
  vertical position; if detection is ambiguous, page is flagged suspect in the manifest.
- Tables: degrade to text lines; page flagged suspect so a human checks them.
- Hyphenation at line end: rejoined only when the joined word loses the hyphen
  (conservative: keep hyphen if the fragment looks like a real hyphenated compound).
- Empty pages (art-only): produce an empty `.txt`, flagged suspect.
- Password-protected PDF: exit 1 with message naming the file and the reason.
- Scanned PDF (no text layer): exit 1 advising that OCR is not supported in v1.

## Links
- Workflow: `workflows/ingest-pdf.md`
- Tool: `tools/extract_pdf.py` (PyMuPDF; pdfplumber only as fallback for table grids
  if PyMuPDF proves insufficient — decide per-book, record the decision here)
- Tests: manual verification against the real PDFs (none committed; see workflow)
- Related specs: `specs/content-schema.md` (the target format downstream)
