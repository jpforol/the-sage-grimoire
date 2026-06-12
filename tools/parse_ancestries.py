#!/usr/bin/env python3
"""Parse the Ancestralidades supplement into codex entries.

Deterministic implementation of specs/ancestry-parser.md:
    python tools/parse_ancestries.py [--src .tmp/extracted/ancestralidades]

Per ancestry spread (2 pages): one ancestralidades entry (lore + traços) and
one trilhas entry (subcategory ancestralidade, níveis 1/2/5). Anomaly report
at .tmp/ancestry-parse-report.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_entries import slugify

FURNITURE_RE = re.compile(r"^(Licenciado para .*|\d{1,3})\s*$")
TRACOS_RE = re.compile(r"^Traços d[eao] ([A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç ]+?)\s*$")
NIVEL_RE = re.compile(r"^(.+?) de Nível (\d)\s*$")
# 'Nome do Talento: texto' → paragraph break + bold lead.
TRAIT_LEAD_RE = re.compile(r"^([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^:.!?]{1,45}):\s+(.+)$")
BULLET_RE = re.compile(r"^([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^:•]{1,60})\s*:\s+(.+)$")
STAT_KEYS = {
    "Vida": "vida",
    "Tamanho": "tamanho",
    "Velocidade": "velocidade",
    "Sentidos": "sentidos",
    "Idiomas Bônus": "idiomas_bonus",
}
SMALL_WORDS = {"de", "da", "das", "do", "dos", "e", "a", "o", "as", "os", "em", "com", "na", "no", "pelas", "pelos", "que", "se"}


def is_heading(line: str) -> bool:
    s = line.strip()
    if not (4 <= len(s) <= 40) or s[-1] in ".:,;!?" or s.endswith("-"):
        return False
    words = s.split()
    if not (2 <= len(words) <= 6):
        return False
    return all(w[0].isupper() or w.lower() in SMALL_WORDS for w in words)


def load_pages(src: Path) -> dict[int, list[str]]:
    pages: dict[int, list[str]] = {}
    for path in sorted(src.glob("page-*.txt")):
        n = int(path.stem.split("-")[1])
        pages[n] = [
            ln.rstrip()
            for ln in path.read_text(encoding="utf-8").splitlines()
            if not FURNITURE_RE.match(ln.strip())
        ]
    return pages


def reflow(lines: list[str], bold_leads: bool = True) -> str:
    """Join wrapped lines into paragraphs; trait leads start new bold paragraphs.

    Also detects • bullets and converts them to Markdown * lists.
    """
    paragraphs: list[str] = []
    current: list[str] = []

    def push() -> None:
        if not current:
            return
        para = " ".join(" ".join(current).split())
        current.clear()
        if "•" not in para:
            paragraphs.append(para)
            return
        # Bullet-separated list: split intro from items
        parts = [p.strip() for p in re.split(r"\s*•\s*", para) if p.strip()]
        intro = parts[0]
        items = []
        for part in parts[1:]:
            m = BULLET_RE.match(part)
            items.append(f"* **{m.group(1).strip()}:** {m.group(2)}" if m else f"* {part}")
        if intro:
            paragraphs.append(intro)
        if items:
            paragraphs.append("\n".join(items))

    for line in lines:
        s = line.strip()
        if not s:
            push()
            continue
        m = TRAIT_LEAD_RE.match(s) if bold_leads else None
        if m:
            push()
            lead = m.group(1)
            lead = lead.title() if lead.isupper() else lead
            current.append(f"**{lead}:** {m.group(2)}")
        elif is_heading(s):
            push()
            paragraphs.append(f"## {s}")
        else:
            current.append(s)
    push()
    return "\n\n".join(paragraphs)


def parse_stats(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    """Split the leading stat lines of a traços block from the trait text."""
    stats: dict[str, str] = {}
    rest_start = 0
    for i, line in enumerate(lines):
        parts = [p.strip() for p in line.split(",")]
        matched = False
        for part in parts:
            m = re.match(r"^([A-Za-zÁÉÍÓÚÂÊÔÃÕÇãõéíóúâêôç ]+):\s*(.+)$", part)
            if m and m.group(1).strip() in STAT_KEYS:
                stats[STAT_KEYS[m.group(1).strip()]] = m.group(2).strip()
                matched = True
        if not matched:
            rest_start = i
            break
        rest_start = i + 1
    return stats, lines[rest_start:]


def first_sentence(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    m = re.match(r"(.+?[.!?])\s", text + " ")
    s = m.group(1) if m else text
    return (s[: limit - 1] + "…") if len(s) > limit else s


def yaml_quote(s: str) -> str:
    return '"' + s.replace('"', "'") + '"'


def render(frontmatter: dict, body: str) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, (dict, list)) and not value:
            continue
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v if isinstance(v, int) else yaml_quote(str(v))}")
        elif isinstance(value, list):
            lines.append(f"{key}: [{', '.join(yaml_quote(v) for v in value)}]")
        else:
            lines.append(f"{key}: {value if isinstance(value, int) else yaml_quote(str(value))}")
    lines += ["---", "", body, ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=Path(".tmp/extracted/ancestralidades"))
    parser.add_argument("--out", type=Path, default=Path("src/content/codex"))
    args = parser.parse_args()

    pages = load_pages(args.src)
    anomalies: list[dict] = []

    # Discover ancestries from 'Traços de X' markers.
    spreads: list[tuple[str, int]] = []  # (name, marker file page)
    for n, lines in sorted(pages.items()):
        for line in lines:
            m = TRACOS_RE.match(line.strip())
            if m:
                spreads.append((m.group(1), n))

    anc_dir = args.out / "ancestralidades"
    tri_dir = args.out / "trilhas"
    anc_dir.mkdir(parents=True, exist_ok=True)
    tri_dir.mkdir(parents=True, exist_ok=True)
    for old in anc_dir.glob("*.md"):
        old.unlink()
    for old in tri_dir.glob("trilha-de-*.md"):
        old.unlink()

    for name, marker_page in spreads:
        book_page = marker_page - 2  # file page-N = book page N-1; spread starts a page earlier
        lines = pages.get(marker_page - 1, []) + pages[marker_page]

        idx_tracos = next(
            i for i, ln in enumerate(lines) if TRACOS_RE.match(ln.strip())
        )
        idx_lvl1 = next(
            (
                i
                for i, ln in enumerate(lines)
                if NIVEL_RE.match(ln.strip())
                and NIVEL_RE.match(ln.strip()).group(2) == "1"
            ),
            None,
        )

        # Drop the big title line (first occurrence of the bare name).
        lore_lines = lines[:idx_tracos]
        for i, ln in enumerate(lore_lines):
            if ln.strip() == name:
                lore_lines = lore_lines[:i] + lore_lines[i + 1 :]
                break

        tracos_end = idx_lvl1 if idx_lvl1 is not None else len(lines)
        stats, trait_lines = parse_stats(lines[idx_tracos + 1 : tracos_end])

        body = reflow(lore_lines) + "\n\n## Traços\n\n" + reflow(trait_lines)
        summary = first_sentence(reflow(lore_lines, bold_leads=False))
        entry = render(
            {
                "title": name,
                "category": "ancestralidades",
                "summary": summary,
                "stats": stats,
                "source": {"book": "ancestralidades", "page": book_page},
            },
            body,
        )
        (anc_dir / f"{slugify(name)}.md").write_text(entry, encoding="utf-8")

        if idx_lvl1 is None:
            anomalies.append({"page": book_page, "issue": f"'{name} de Nível 1' não encontrado"})
            continue

        # Trilha body: replace 'X de Nível N' markers with '## Nível N' headings.
        trilha_lines: list[str] = []
        for ln in lines[idx_lvl1:]:
            m = NIVEL_RE.match(ln.strip())
            if m and m.group(1) == name:
                trilha_lines.append("")
                trilha_lines.append(f"## Nível {m.group(2)}")
                trilha_lines.append("")
            else:
                trilha_lines.append(ln)
        # Stray trailing column artifacts equal to the bare name.
        trilha_lines = [ln for ln in trilha_lines if ln.strip() != name]

        trilha_entry = render(
            {
                "title": f"Trilha de {name}",
                "category": "trilhas",
                "subcategory": "ancestralidade",
                "summary": f"A trilha de ancestralidade de {name}: níveis 1, 2 e 5.",
                "tags": ["ancestralidade"],
                "source": {"book": "ancestralidades", "page": book_page + 1},
            },
            reflow(trilha_lines),
        )
        (tri_dir / f"trilha-de-{slugify(name)}.md").write_text(
            trilha_entry, encoding="utf-8"
        )

    report = {"ancestries": len(spreads), "anomalies": anomalies}
    Path(".tmp/ancestry-parse-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"OK: {len(spreads)} ancestralidades + trilhas → {args.out} "
        f"({len(anomalies)} anomalia(s))"
    )


if __name__ == "__main__":
    main()
