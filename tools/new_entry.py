#!/usr/bin/env python3
"""Scaffold a valid codex entry (specs/content-schema.md).

Usage:
    python tools/new_entry.py magias "Bola de Fogo" --tags fogo,evocação
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from validate_entries import CATEGORIES, slugify

TEMPLATE = """---
title: "{title}"
category: "{category}"
summary: "TODO: resumo de uma linha mostrado nas listagens."
tags: [{tags}]
stats:
  exemplo: "valor"
draft: true
---

Corpo da entrada em Markdown.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("category", choices=sorted(CATEGORIES))
    parser.add_argument("title")
    parser.add_argument("--tags", default="", help="tags separadas por vírgula")
    args = parser.parse_args()

    slug = slugify(args.title)
    if not slug:
        sys.exit(f"Título não gera um slug válido: '{args.title}'")

    dest = Path("src/content/codex") / args.category / f"{slug}.md"
    if dest.exists():
        sys.exit(f"Já existe: {dest}")

    tags = ", ".join(
        f'"{t.strip().lower()}"' for t in args.tags.split(",") if t.strip()
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        TEMPLATE.format(title=args.title, category=args.category, tags=tags),
        encoding="utf-8",
    )
    print(f"Criado: {dest} (draft: true — publique removendo o draft)")


if __name__ == "__main__":
    main()
