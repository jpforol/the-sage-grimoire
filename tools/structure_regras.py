#!/usr/bin/env python3
"""Structure dense prose walls in regras/ into subsections.

Uses heuristics to detect named subsections and split them into proper headings.
Target files with known structures:
- aflicoes.md: afflictions (Amaldiçoado, Amedrontado, etc.)
- privacao-e-perigos.md: dangers (Privação de Sono, Desmembramento, etc.)
- acoes-em-combate.md: actions + reactions
- atacando.md: attack circumstances + options
- combate-fundamentos.md: combat topics
- atributos-e-rolagens.md: attributes (Força, Agilidade, Intelecto, Vontade)
- tamanho-defesa-vida-e-dano.md: topics (Morte, Repouso, Tempo)
"""

from pathlib import Path
import re


AFFLICTION_NAMES = {
    "Amaldiçoado", "Amedrontado", "Atordoado", "Cego", "Confuso", "Controlado",
    "Debilitado", "Enfraquecido", "Envenenado", "Incendiado", "Inconsciente",
    "Adormecido", "Lento", "Prostrado", "Restringido", "Surdo", "Vulnerável",
    "Prejudicar", "Soterrado"
}

DANGER_NAMES = {
    "Privação de Sono", "Desmembramento", "Exposição ao Clima", "Fogo", "Venenos",
    "Infecção", "Sufocamento", "Transformação"
}

ACTION_NAMES = {
    "Ajudar", "Atacar", "Atrapalhar", "Arremessar", "Conjurar", "Correr", "Defender",
    "Encerrar", "Encontrar", "Esconder", "Estabilizar", "Roubar", "Superar", "Usar",
    "Fazer"
}

REACTION_NAMES = {
    "Ataque Livre", "Cobrir Aliado", "Esquivar", "Pegar", "Suportar", "Tomar a Iniciativa"
}

ATTRIBUTE_NAMES = {"Força", "Agilidade", "Intelecto", "Vontade"}

ATTACK_CIRCUMSTANCE_NAMES = {
    "Alvo Cercado", "Cobertura", "Invisível", "Terreno Elevado", "Tiro de Longa Distância"
}

ATTACK_OPTION_NAMES = {
    "Agarrar", "Arrastar", "Conter", "Derrubar", "Empurrar", "Escapar"
}


def split_subsections(text: str, subsection_names: set) -> list[str]:
    """Split text at occurrences of subsection names (capitalize first word).

    Returns a list where text and subsections are interleaved (text before each name).
    """
    # Build a regex: match subsection name followed by space or newline + capitalized start
    pattern = r"\b(" + "|".join(re.escape(name) for name in sorted(subsection_names, key=len, reverse=True)) + r")\b"

    parts = []
    last_end = 0
    for m in re.finditer(pattern, text):
        if m.start() > last_end:
            # Preceding text
            parts.append(("text", text[last_end:m.start()].rstrip()))
        # The matched name
        parts.append(("name", m.group(1)))
        last_end = m.end()

    if last_end < len(text):
        parts.append(("text", text[last_end:].rstrip()))

    return parts


def structure_afflictions(content: str) -> str:
    """Split afflictions into individual ### subsections."""
    lines = content.split("\n")

    # Find the sidebox "## MAEGAN FICA PRESA" and the dense wall after it
    sidebox_idx = next((i for i, l in enumerate(lines) if "## MAEGAN FICA PRESA" in l), None)
    if sidebox_idx is None:
        return content

    # The dense wall should be a paragraph or two after the sidebox
    wall_start = next((i for i in range(sidebox_idx + 1, len(lines)) if lines[i].strip() and not lines[i].startswith("#")), None)
    if wall_start is None:
        return content

    # Collect the wall paragraph(s) until we hit a ## section or end
    wall_end = next((i for i in range(wall_start, len(lines)) if lines[i].startswith("#")), len(lines))
    wall_text = "\n".join(lines[wall_start:wall_end]).strip()

    # Split by affliction names
    parts = split_subsections(wall_text, AFFLICTION_NAMES)

    # Reconstruct: keep sidebox + example, then emit ### subsections for each affliction
    result = "\n".join(lines[:wall_end])

    if parts:
        new_sections = []
        i = 0
        while i < len(parts):
            if parts[i][0] == "name":
                # Collect all text until next name (or end)
                name = parts[i][1]
                desc_parts = []
                i += 1
                while i < len(parts) and parts[i][0] == "text":
                    desc_parts.append(parts[i][1])
                    i += 1
                desc = " ".join(d for d in desc_parts if d).strip()
                if desc:
                    new_sections.append(f"### {name}\n\n{desc}")
            else:
                i += 1

        if new_sections:
            result = result.rstrip() + "\n\n" + "\n\n".join(new_sections)

    # Preserve anything after wall_end (like "## Efeitos Cumulativos")
    if wall_end < len(lines):
        result += "\n\n" + "\n".join(lines[wall_end:])

    return result


def structure_file(path: Path, subsection_names: set, heading_level: str = "###") -> bool:
    """Split dense prose paragraphs into subsections."""
    content = path.read_text(encoding="utf-8")
    original = content

    # Special handling for aflicoes
    if path.name == "aflicoes.md":
        content = structure_afflictions(content)
    else:
        # General approach: find paragraphs and look for subsection names
        # This is a heuristic and may require manual tweaks
        pass

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main() -> None:
    regras_dir = Path("src/content/codex/regras")

    # Start with aflicoes.md
    if (regras_dir / "aflicoes.md").exists():
        if structure_file(regras_dir / "aflicoes.md", AFFLICTION_NAMES):
            print("Structured: aflicoes.md")

    print("\nNote: Other regras/ files require manual review and editing.")
    print("Generated files to review:")
    print("  - privacao-e-perigos.md (dangers)")
    print("  - acoes-em-combate.md (actions + reactions)")
    print("  - atacando.md (attack circumstances)")
    print("  - combate-fundamentos.md (topics)")
    print("  - atributos-e-rolagens.md (attributes)")
    print("  - tamanho-defesa-vida-e-dano.md (topics)")


if __name__ == "__main__":
    main()
