"""Tests for tools/validate_entries.py (specs/content-schema.md)."""

import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validate_entries import slugify, validate_entry, validate_tree


def write_entry(root: Path, category: str, slug: str, frontmatter: str) -> Path:
    path = root / category / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n{textwrap.dedent(frontmatter).strip()}\n---\nCorpo.\n",
        encoding="utf-8",
    )
    return path


VALID = """
    title: "Bola de Fogo"
    category: "magias"
    summary: "Uma explosão de chamas."
    tags: ["fogo", "evocação"]
    stats:
      circulo: 3
      alcance: "45 metros"
    source:
      book: "livro-do-jogador"
      page: 142
    draft: false
"""


class TestSlugify:
    def test_folds_accents_and_cedilla(self):
        assert slugify("Coração de Dragão") == "coracao-de-dragao"

    def test_collapses_punctuation(self):
        assert slugify("Combate: Iniciativa e Turnos!") == "combate-iniciativa-e-turnos"


class TestValidateEntry:
    def test_valid_entry_passes(self, tmp_path):
        path = write_entry(tmp_path, "magias", "bola-de-fogo", VALID)
        assert validate_entry(path, tmp_path) == []

    def test_missing_title_fails(self, tmp_path):
        path = write_entry(
            tmp_path,
            "magias",
            "sem-titulo",
            'category: "magias"\nsummary: "Resumo."',
        )
        errors = validate_entry(path, tmp_path)
        assert any("'title'" in e for e in errors)

    def test_bad_category_fails(self, tmp_path):
        path = write_entry(
            tmp_path,
            "magias",
            "categoria-ruim",
            'title: "X"\ncategory: "feiticos"\nsummary: "Resumo."',
        )
        errors = validate_entry(path, tmp_path)
        assert any("'category'" in e for e in errors)

    def test_category_folder_mismatch_fails(self, tmp_path):
        path = write_entry(
            tmp_path,
            "itens",
            "pasta-errada",
            'title: "X"\ncategory: "magias"\nsummary: "Resumo."',
        )
        errors = validate_entry(path, tmp_path)
        assert any("não corresponde à pasta" in e for e in errors)

    def test_uppercase_tag_fails(self, tmp_path):
        path = write_entry(
            tmp_path,
            "magias",
            "tag-maiuscula",
            'title: "X"\ncategory: "magias"\nsummary: "R."\ntags: ["Fogo"]',
        )
        errors = validate_entry(path, tmp_path)
        assert any("minúscula" in e for e in errors)

    def test_unknown_key_fails(self, tmp_path):
        path = write_entry(
            tmp_path,
            "magias",
            "chave-errada",
            'title: "X"\ncategory: "magias"\nsummary: "R."\nsumary: "typo"',
        )
        errors = validate_entry(path, tmp_path)
        assert any("desconhecidas" in e for e in errors)

    def test_accented_slug_fails(self, tmp_path):
        path = write_entry(
            tmp_path,
            "magias",
            "feitiço",
            'title: "Feitiço"\ncategory: "magias"\nsummary: "R."',
        )
        errors = validate_entry(path, tmp_path)
        assert any("slug" in e for e in errors)

    def test_nested_stats_fails(self, tmp_path):
        path = write_entry(
            tmp_path,
            "magias",
            "stats-aninhado",
            'title: "X"\ncategory: "magias"\nsummary: "R."\nstats:\n  dano:\n    base: 8',
        )
        errors = validate_entry(path, tmp_path)
        assert any("escalar" in e for e in errors)

    def test_bad_source_page_fails(self, tmp_path):
        path = write_entry(
            tmp_path,
            "magias",
            "pagina-ruim",
            'title: "X"\ncategory: "magias"\nsummary: "R."\nsource:\n  book: "livro"\n  page: 0',
        )
        errors = validate_entry(path, tmp_path)
        assert any("source.page" in e for e in errors)


class TestValidateTree:
    def test_valid_tree_exits_zero(self, tmp_path):
        write_entry(tmp_path, "magias", "bola-de-fogo", VALID)
        assert validate_tree(tmp_path) == 0

    def test_duplicate_slug_across_categories_fails(self, tmp_path):
        write_entry(tmp_path, "magias", "duplicado", VALID)
        write_entry(
            tmp_path,
            "itens",
            "duplicado",
            'title: "Y"\ncategory: "itens"\nsummary: "R."',
        )
        assert validate_tree(tmp_path) == 1

    def test_empty_tree_fails(self, tmp_path):
        assert validate_tree(tmp_path) == 1
