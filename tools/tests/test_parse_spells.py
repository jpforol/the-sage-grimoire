"""Tests for tools/parse_spells.py (specs/spell-parser.md)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parse_spells import is_all_caps_name, parse, pt_title, first_sentence


def lines_of(page: int, text: str) -> list[tuple[int, str]]:
    return [(page, line) for line in text.strip().splitlines()]


FIXTURE = lines_of(
    80,
    """
Pirosofia
O fogo responde a quem ousa chamá-lo pelo nome.
Os pirósofos dominam a chama em todas as suas formas.
Novato de Pirosofia
CHAMAS RELUZENTES
CONJURAÇÕES: 1
ALVO: Uma criatura a até 10 metros de distância
DURAÇÃO: Instantânea
Fogo arcano salta da sua mão. O alvo sofre 2d6 de dano.
Em um sucesso crítico, o dano dobra.
Especialista de Pirosofia
MURALHA DE FOGO
CONJURAÇÕES: 2
ALVO: Um ponto no espaço
DURAÇÃO: 1 minuto
Uma parede de chamas se ergue do chão.
Mestre de Pirosofia
CORAÇÃO DA FORNALHA
CONJURAÇÕES: 1
ALVO: Você
DURAÇÃO: 1 hora
Seu corpo vira fogo vivo.
""",
)


class TestHelpers:
    def test_pt_title_keeps_small_words_lower(self):
        assert pt_title("CORAÇÃO DA FORNALHA") == "Coração da Fornalha"
        assert pt_title("CERTEZA DOS TOLOS") == "Certeza dos Tolos"

    def test_all_caps_detection(self):
        assert is_all_caps_name("MURALHA DE FOGO")
        assert not is_all_caps_name("Especialista de Pirosofia")
        assert not is_all_caps_name("FEITIÇOS DE EVOCAÇÃO:")  # sidebar title

    def test_first_sentence_truncates(self):
        s = first_sentence("Primeira frase. Segunda frase.")
        assert s == "Primeira frase."


class TestParse:
    def test_parses_traditions_spells_and_ranks(self):
        traditions, spells, anomalies = parse(FIXTURE)

        assert [t.name for t in traditions] == ["Pirosofia"]
        assert "ousa chamá-lo" in " ".join(traditions[0].intro)

        assert [s.name for s in spells] == [
            "Chamas Reluzentes",
            "Muralha de Fogo",
            "Coração da Fornalha",
        ]
        assert [s.rank for s in spells] == ["novato", "especialista", "mestre"]

        first = spells[0]
        assert first.tradition == "Pirosofia"
        assert first.page == 80
        assert first.stats["conjuracoes"] == 1
        assert first.stats["alvo"].startswith("Uma criatura")
        assert first.stats["duracao"] == "Instantânea"
        assert "2d6 de dano" in " ".join(first.body)

    def test_wrapped_caps_name_is_merged(self):
        _, spells, _ = parse(
            lines_of(
                80,
                "Pirosofia\nIntro.\nZUMBIDO\nDA HOSTE\nCONJURAÇÕES: 1\nALVO: Você\n"
                "DURAÇÃO: 1 hora\nCorpo.\nEspecialista de Pirosofia\nMURALHA\n"
                "CONJURAÇÕES: 1\nALVO: Você\nDURAÇÃO: 1 hora\nCorpo.\n"
                "Mestre de Pirosofia",
            )
        )
        assert spells[0].name == "Zumbido da Hoste"

    def test_false_tradition_mention_in_text_ignored(self):
        # 'Aeromancia' standalone inside Pirosofia's intro must not split sections
        traditions, spells, _ = parse(
            lines_of(
                80,
                "Pirosofia\nIntro da tradição.\nAeromancia\nmencionada em tabela.\n"
                "FOGO\nCONJURAÇÕES: 1\nALVO: Você\nDURAÇÃO: 1 hora\nCorpo.\n"
                "Especialista de Pirosofia\nMURALHA\nCONJURAÇÕES: 1\nALVO: Você\n"
                "DURAÇÃO: 1 hora\nCorpo.\nMestre de Pirosofia",
            )
        )
        assert [t.name for t in traditions] == ["Pirosofia"]
        assert [s.tradition for s in spells] == ["Pirosofia", "Pirosofia"]

    def test_sidebar_caps_line_folded_into_body(self):
        _, spells, _ = parse(
            lines_of(
                80,
                "Pirosofia\nIntro.\nFOGO\nCONJURAÇÕES: 1\nALVO: Você\nDURAÇÃO: 1 hora\n"
                "Corpo do feitiço.\nTRUQUES DE SALÃO\nTexto de box lateral sem stats.\n"
                "Especialista de Pirosofia\nMURALHA\nCONJURAÇÕES: 1\nALVO: Você\n"
                "DURAÇÃO: 1 hora\nCorpo.\nMestre de Pirosofia",
            )
        )
        assert [s.name for s in spells] == ["Fogo", "Muralha"]
        assert any("Truques de Salão" in b for b in spells[0].body)
