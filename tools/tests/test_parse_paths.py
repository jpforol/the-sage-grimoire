"""Tests for tools/parse_paths.py (specs/path-parser.md)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parse_paths import LEVEL_RE, parse_region


def lines_of(page: int, text: str) -> list[tuple[int, str]]:
    return [(page, line) for line in text.strip().splitlines()]


class TestLevelHeader:
    def test_matches_path_level_lines(self):
        m = LEVEL_RE.match("Amoque Nível 3")
        assert m.group(1) == "Amoque" and m.group(2) == "3"
        m = LEVEL_RE.match("Portador da Lâmina Negra Nível 10")
        assert m.group(1) == "Portador da Lâmina Negra"

    def test_rejects_prose(self):
        assert LEVEL_RE.match("você recebe os benefícios de nível 3 dessa trilha") is None


class TestParseRegion:
    def test_two_paths_with_levels(self):
        anomalies: list[dict] = []
        paths = parse_region(
            lines_of(
                170,
                "Amoque\nA fúria toma conta de você.\nAmoque Nível 3\nVida: +6\n"
                "Fúria: Você ataca com 1 dádiva.\nAmoque Nível 6\nVida: +6\n"
                "Espadachim\nSua lâmina é uma extensão do braço.\n"
                "Espadachim Nível 3\nVida: +4\nEspadachim Nível 6\nVida: +4",
            ),
            anomalies,
        )
        assert [p["name"] for p in paths] == ["Amoque", "Espadachim"]
        assert [lv for lv, _ in paths[0]["levels"]] == ["3", "6"]
        assert "fúria toma conta" in " ".join(paths[0]["intro"]).lower()
        # Amoque's body must not bleed into Espadachim's intro
        assert not any("Espadachim" in ln for ln in paths[0]["intro"])
        assert anomalies == []

    def test_single_header_name_is_filtered(self):
        anomalies: list[dict] = []
        paths = parse_region(
            lines_of(
                170,
                "Amoque\nIntro.\nAmoque Nível 3\nVida: +6\nFalso Nível 9\n"
                "Amoque Nível 6\nVida: +6",
            ),
            anomalies,
        )
        assert [p["name"] for p in paths] == ["Amoque"]
        assert any("nível único" in a["issue"] for a in anomalies)

    def test_wrapped_heading_found(self):
        anomalies: list[dict] = []
        paths = parse_region(
            lines_of(
                274,
                "Portador da\nLâmina Negra\nAnor forjou a Lâmina Negra.\n"
                "Portador da Lâmina Negra Nível 7\nVida: +12\n"
                "Portador da Lâmina Negra Nível 10\nVida: +12",
            ),
            anomalies,
        )
        assert paths[0]["name"] == "Portador da Lâmina Negra"
        assert paths[0]["intro"] == ["Anor forjou a Lâmina Negra."]
        assert anomalies == []
