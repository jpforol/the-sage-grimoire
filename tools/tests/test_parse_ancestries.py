"""Tests for tools/parse_ancestries.py (specs/ancestry-parser.md)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parse_ancestries import TRACOS_RE, is_heading, parse_stats, reflow


class TestMarkers:
    def test_tracos_marker_matches_clean_name(self):
        assert TRACOS_RE.match("Traços de Anão").group(1) == "Anão"
        assert TRACOS_RE.match("Traços do Warg").group(1) == "Warg"

    def test_tracos_marker_rejects_toc_dotted_lines(self):
        assert TRACOS_RE.match("Traços de Anão.......................5") is None


class TestHeading:
    def test_title_case_section_is_heading(self):
        assert is_heading("Reinos Caídos")
        assert is_heading("Aventureiros Anões")

    def test_wrapped_body_line_is_not_heading(self):
        assert not is_heading("os anões estavam entre os")
        assert not is_heading("Vida na Montanha.")


class TestReflow:
    def test_trait_leads_become_bold_paragraphs(self):
        text = reflow(
            [
                "Alvo Difícil: Você impõe 1 revés em rolagens",
                "de ataque contra você.",
                "Pernas Curtas: Quando você corre, você somente",
                "dobra o seu valor de Velocidade.",
            ]
        )
        assert "**Alvo Difícil:** Você impõe 1 revés em rolagens de ataque contra você." in text
        assert "**Pernas Curtas:**" in text

    def test_headings_split_paragraphs(self):
        text = reflow(["texto antes", "Reinos Caídos", "texto depois"])
        assert "## Reinos Caídos" in text


class TestParseStats:
    def test_stat_lines_split_from_traits(self):
        stats, rest = parse_stats(
            [
                "Vida: +4",
                "Tamanho: 1/2, Velocidade: 5",
                "Sentidos: Visão no Escuro",
                "Idiomas Bônus: Anânico",
                "Alvo Difícil: Você impõe 1 revés.",
            ]
        )
        assert stats == {
            "vida": "+4",
            "tamanho": "1/2",
            "velocidade": "5",
            "sentidos": "Visão no Escuro",
            "idiomas_bonus": "Anânico",
        }
        assert rest == ["Alvo Difícil: Você impõe 1 revés."]
