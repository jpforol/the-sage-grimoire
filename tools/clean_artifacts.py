#!/usr/bin/env python3
"""Remove stray page-header artifacts from trilhas MD files.

One-off cleanup for leaked running headers and chapter section names.
"""

from pathlib import Path
import re


def clean_file(path: Path) -> bool:
    """Return True if file was modified."""
    content = path.read_text(encoding="utf-8")
    original = content
    lines = content.splitlines(keepends=True)

    # Rule 1: Remove "## Trilhas de Especiialista" + everything after (16 especialista files)
    if "## Trilhas de Especiialista" in content:
        idx = next(i for i, ln in enumerate(lines) if "## Trilhas de Especiialista" in ln)
        lines = lines[:idx]

    # Rule 2: Remove orphaned "## Caminhos de Mestre" heading (38 mestre files)
    # Detect: heading followed by blank line(s) then a ## Nível heading
    new_lines = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "## Caminhos de Mestre":
            # Look ahead: skip blanks
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            # If next non-blank is a ## Nível heading, skip the "## Caminhos de Mestre" line
            if j < len(lines) and lines[j].strip().startswith("## Nível"):
                i += 1  # Skip the line
                continue
        new_lines.append(lines[i])
        i += 1
    lines = new_lines

    # Rule 3: Remove bare "Capítulo X" lines
    lines = [ln for ln in lines if not re.match(r"^Capítulo \d+\s*$", ln.strip())]

    # Rule 4: Fix criomante.md — strip "Capítulo 6 " prefix from first body paragraph
    if path.name == "criomante.md":
        new_lines = []
        for ln in lines:
            if ln.startswith("Capítulo 6 "):
                ln = ln[len("Capítulo 6 "):]
            new_lines.append(ln)
        lines = new_lines

    # Rule 5: Fix psiquico.md — remove "## Trilhas de Mestre" heading + everything after
    if path.name == "psiquico.md":
        idx_mestre = next((i for i, ln in enumerate(lines) if ln.strip() == "## Trilhas de Mestre"), None)
        if idx_mestre is not None:
            lines = lines[:idx_mestre]

    # Rejoin and check if changed
    new_content = "".join(lines)
    if new_content != original:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main() -> None:
    trilhas_dir = Path("src/content/codex/trilhas")
    if not trilhas_dir.exists():
        print("trilhas/ directory not found")
        return

    count = 0
    for md_file in sorted(trilhas_dir.glob("*.md")):
        if clean_file(md_file):
            count += 1
            print(f"Cleaned: {md_file.name}")

    print(f"\nTotal files modified: {count}")


if __name__ == "__main__":
    main()
