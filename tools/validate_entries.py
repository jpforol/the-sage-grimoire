#!/usr/bin/env python3
"""Validate codex entries against specs/content-schema.md.

Usage:
    python tools/validate_entries.py src/content/codex/

Exit code 0 when every entry is valid; 1 with per-file messages otherwise.
Mirrors the Zod schema in src/content.config.ts — keep both in sync.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import frontmatter

CATEGORIES = {"classes", "magias", "itens", "regras"}
ALLOWED_KEYS = {"title", "category", "summary", "tags", "stats", "source", "draft"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def slugify(title: str) -> str:
    """ASCII-fold, lowercase, hyphens — the slug rule from the schema spec."""
    folded = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")


def validate_entry(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    try:
        post = frontmatter.load(path)
    except Exception as exc:
        return [f"frontmatter ilegível: {exc}"]

    meta = post.metadata

    unknown = set(meta) - ALLOWED_KEYS
    if unknown:
        errors.append(f"chaves desconhecidas no frontmatter: {sorted(unknown)}")

    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("'title' obrigatório (string não vazia)")

    summary = meta.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("'summary' obrigatório (string não vazia)")

    category = meta.get("category")
    if category not in CATEGORIES:
        errors.append(f"'category' deve ser uma de {sorted(CATEGORIES)}: '{category}'")
    else:
        parent = path.relative_to(root).parts[0]
        if parent != category:
            errors.append(
                f"'category' ({category}) não corresponde à pasta ({parent})"
            )

    slug = path.stem
    if not SLUG_RE.match(slug):
        suggestion = slugify(title) if isinstance(title, str) else "?"
        errors.append(
            f"nome de arquivo inválido como slug: '{slug}' (sugestão: '{suggestion}')"
        )

    tags = meta.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        errors.append("'tags' deve ser uma lista de strings")
    else:
        for tag in tags:
            if tag != tag.lower():
                errors.append(f"tag deve ser minúscula: '{tag}' → '{tag.lower()}'")

    stats = meta.get("stats", {})
    if not isinstance(stats, dict):
        errors.append("'stats' deve ser um mapa de chave/valor")
    else:
        for key, value in stats.items():
            if not isinstance(value, (str, int, float, bool)):
                errors.append(
                    f"stats.{key}: valor deve ser escalar (string/número/booleano)"
                )

    source = meta.get("source")
    if source is not None:
        if not isinstance(source, dict):
            errors.append("'source' deve ser um mapa com 'book' e 'page'")
        else:
            book = source.get("book")
            page = source.get("page")
            if not isinstance(book, str) or not book.strip():
                errors.append("source.book obrigatório (string não vazia)")
            if not isinstance(page, int) or page < 1:
                errors.append("source.page deve ser inteiro positivo")
            extra = set(source) - {"book", "page"}
            if extra:
                errors.append(f"chaves desconhecidas em 'source': {sorted(extra)}")

    draft = meta.get("draft", False)
    if not isinstance(draft, bool):
        errors.append("'draft' deve ser booleano")

    return errors


def validate_tree(root: Path) -> int:
    files = sorted(root.rglob("*.md"))
    if not files:
        print(f"Nenhuma entrada .md encontrada em {root}")
        return 1

    failures = 0
    slugs: dict[str, Path] = {}

    for path in files:
        errors = validate_entry(path, root)

        slug = path.stem
        if slug in slugs:
            errors.append(f"slug duplicado (já usado em {slugs[slug]})")
        else:
            slugs[slug] = path

        if errors:
            failures += 1
            rel = path.relative_to(root)
            print(f"ERRO {rel}:")
            for err in errors:
                print(f"  - {err}")

    valid = len(files) - failures
    print(f"\n{valid}/{len(files)} entradas válidas.")
    return 1 if failures else 0


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("src/content/codex")
    if not root.is_dir():
        sys.exit(f"Diretório não encontrado: {root}")
    sys.exit(validate_tree(root))


if __name__ == "__main__":
    main()
