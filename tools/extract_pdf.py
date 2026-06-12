#!/usr/bin/env python3
"""Extract raw text from a source PDF, page by page, in reading order.

Deterministic half of the ingestion pipeline (specs/pdf-extraction-pipeline.md):
    python tools/extract_pdf.py sources/<book>.pdf --out .tmp/extracted/<book>/

Outputs:
    <out>/page-NNN.txt    one plain-text file per page, blocks in reading order
    <out>/manifest.json   page count, per-page stats, suspect-page flags
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:  # pragma: no cover
    sys.exit("PyMuPDF não instalado. Rode: pip install -r tools/requirements.txt")

# Pages with fewer extracted characters than this are flagged for human review
# (likely art-only, table-heavy, or a scan).
LOW_TEXT_THRESHOLD = 80


def order_blocks(blocks: list[tuple], page_width: float) -> tuple[list[tuple], bool]:
    """Sort text blocks into reading order; detect two-column layouts.

    Returns (ordered_blocks, ambiguous) where ambiguous=True means the column
    split was unclear and the page should be flagged suspect.
    """
    text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
    if not text_blocks:
        return [], False

    mid = page_width / 2
    left = [b for b in text_blocks if (b[0] + b[2]) / 2 < mid]
    right = [b for b in text_blocks if (b[0] + b[2]) / 2 >= mid]

    # Two-column page: both halves populated and no block spans the middle.
    spanning = [b for b in text_blocks if b[0] < mid * 0.8 and b[2] > mid * 1.2]
    two_columns = bool(left) and bool(right) and len(spanning) <= len(text_blocks) * 0.3

    if two_columns:
        ordered = sorted(spanning, key=lambda b: b[1])
        non_spanning_left = sorted(
            (b for b in left if b not in spanning), key=lambda b: b[1]
        )
        non_spanning_right = sorted(
            (b for b in right if b not in spanning), key=lambda b: b[1]
        )
        ambiguous = 0 < len(spanning) <= len(text_blocks) * 0.3
        return ordered + non_spanning_left + non_spanning_right, ambiguous

    return sorted(text_blocks, key=lambda b: (b[1], b[0])), False


def dehyphenate(text: str) -> str:
    """Rejoin words hyphenated at line breaks: 'fei-\\ntiço' -> 'feitiço'.

    Conservative: only joins when both fragments are lowercase letters,
    so real hyphenated compounds at line end mostly survive.
    """
    return re.sub(r"([a-záéíóúâêôãõàç])-\n([a-záéíóúâêôãõàç])", r"\1\2", text)


def extract(pdf_path: Path, out_dir: Path) -> dict:
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as exc:
        sys.exit(f"Não foi possível abrir '{pdf_path}': {exc}")

    if doc.needs_pass:
        sys.exit(
            f"'{pdf_path.name}' está protegido por senha — remova a proteção e tente de novo."
        )

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    pages = []
    total_chars = 0

    for i, page in enumerate(doc, start=1):
        blocks, ambiguous = order_blocks(page.get_text("blocks"), page.rect.width)
        text = dehyphenate("\n".join(b[4].rstrip() for b in blocks))
        total_chars += len(text)

        reasons = []
        if len(text) < LOW_TEXT_THRESHOLD:
            reasons.append("pouco texto (página de arte, tabela ou digitalizada?)")
        if ambiguous:
            reasons.append("layout de colunas ambíguo — confira a ordem de leitura")

        (out_dir / f"page-{i:03d}.txt").write_text(text, encoding="utf-8")
        pages.append(
            {
                "page": i,
                "chars": len(text),
                "blocks": len(blocks),
                "suspect": bool(reasons),
                "reasons": reasons,
            }
        )

    doc.close()

    if total_chars == 0:
        shutil.rmtree(out_dir)
        sys.exit(
            f"'{pdf_path.name}' não tem camada de texto (PDF digitalizado?). "
            "OCR não é suportado na v1 — veja specs/pdf-extraction-pipeline.md."
        )

    manifest = {
        "source": pdf_path.name,
        "page_count": len(pages),
        "total_chars": total_chars,
        "suspect_pages": [p["page"] for p in pages if p["suspect"]],
        "pages": pages,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="caminho do PDF em sources/")
    parser.add_argument(
        "--out", type=Path, required=True, help="diretório de saída (.tmp/extracted/<book>/)"
    )
    args = parser.parse_args()

    if not args.pdf.is_file():
        sys.exit(f"Arquivo não encontrado: {args.pdf}")

    manifest = extract(args.pdf, args.out)
    suspects = manifest["suspect_pages"]
    print(
        f"OK: {manifest['page_count']} páginas extraídas para {args.out} "
        f"({manifest['total_chars']} caracteres)."
    )
    if suspects:
        print(f"Atenção: {len(suspects)} página(s) suspeita(s): {suspects}")
        print("Revise-as no manifest.json antes de estruturar as entradas.")


if __name__ == "__main__":
    main()
