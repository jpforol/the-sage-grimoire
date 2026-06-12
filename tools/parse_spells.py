#!/usr/bin/env python3
"""Parse the Magias chapter (LivroBasico p76-164) into codex entries.

Deterministic implementation of specs/spell-parser.md:
    python tools/parse_spells.py [--src .tmp/extracted/livro-basico] [--out src/content/codex/magias]

Emits one .md per spell + one intro entry per tradition, and an anomaly report
at .tmp/spell-parse-report.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_entries import slugify

FIRST_PAGE, LAST_PAGE = 76, 164

RANK_HEADER_RE = re.compile(
    r"^(Novato|Especialista|Mestre)\s+(?:(?:de|da|das|do|dos)\s+)?"
    r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w Áá-úÀ-ÿ]{2,30})\s*$"
)
RANK_OF = {"Novato": "novato", "Especialista": "especialista", "Mestre": "mestre"}
# Cósmica is headed by the adjective form ('Novato Cósmicos') — normalize it.
NAME_FIX = {"Cósmicos": "Cósmica"}
# Chapter-index table furniture that the 2-column extraction interleaves into
# the first tradition's intro (specs/spell-parser.md, edge cases).
TABLE_FURNITURE = {"Tradições de Magia", "Tradição", "Descrição"}
STAT_RE = re.compile(r"^(CONJURAÇÕES|ALVO|DURAÇÃO):\s*(.*)$")
# Page furniture and personal-data watermark — never let these into entries.
FURNITURE_RE = re.compile(r"^(Licenciado para .*|Capítulo \d+|\d{1,3})\s*$")

# Words kept lowercase in PT title case.
SMALL_WORDS = {"de", "da", "das", "do", "dos", "e", "a", "o", "as", "os", "em", "com", "para", "na", "no", "nas", "nos", "ao", "à", "um", "uma"}


def pt_title(allcaps: str) -> str:
    words = allcaps.strip().lower().split()
    out = []
    for i, w in enumerate(words):
        out.append(w if (i > 0 and w in SMALL_WORDS) else w.capitalize())
    return " ".join(out)


def is_all_caps_name(line: str) -> bool:
    s = line.strip()
    if not (3 <= len(s) <= 60) or s.endswith(":"):
        return False
    letters = [c for c in s if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


@dataclass
class Spell:
    name: str
    tradition: str
    rank: str
    page: int
    stats: dict = field(default_factory=dict)
    body: list[str] = field(default_factory=list)


@dataclass
class Tradition:
    name: str
    page: int
    intro: list[str] = field(default_factory=list)


def load_lines(src: Path) -> list[tuple[int, str]]:
    """All non-furniture lines of the chapter as (book_page, line)."""
    lines: list[tuple[int, str]] = []
    for page in range(FIRST_PAGE, LAST_PAGE + 1):
        path = src / f"page-{page:03d}.txt"
        if not path.is_file():
            sys.exit(f"Falta {path} — rode tools/extract_pdf.py primeiro.")
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not FURNITURE_RE.match(raw.strip()):
                lines.append((page, raw.rstrip()))
    return lines


def find_sections(
    lines: list[tuple[int, str]],
) -> tuple[list[tuple[int, str, str]], list[dict]]:
    """Locate (start_index, tradition, rank) boundaries, anchored on rank headers.

    Rank headers are unambiguous; tradition section starts are found by searching
    for the standalone tradition-name line between the previous tradition's
    'Mestre' header and this tradition's 'Especialista' header. This avoids false
    starts from tradition names mentioned in tables or running text.
    """
    anomalies: list[dict] = []
    headers: list[tuple[int, str, str]] = []  # (line idx, rank, tradition)
    for i, (_, line) in enumerate(lines):
        m = RANK_HEADER_RE.match(line.strip())
        if m:
            headers.append((i, RANK_OF[m.group(1)], NAME_FIX.get(m.group(2), m.group(2))))

    order: list[str] = []
    for _, rank, name in headers:
        if rank == "especialista" and name not in order:
            order.append(name)

    sections: list[tuple[int, str, str]] = []
    prev_bound = 0
    for name in order:
        esp_idx = next(i for i, r, n in headers if r == "especialista" and n == name)
        novato_idx = next(
            (i for i, r, n in headers if r == "novato" and n == name), None
        )
        first_bound = novato_idx if novato_idx is not None else esp_idx
        # Last heading occurrence: the chapter-index table also contains the
        # tradition name, always before the real section heading.
        start = next(
            (
                i
                for i in range(first_bound - 1, prev_bound - 1, -1)
                if lines[i][1].strip() == name and not is_all_caps_name(lines[i][1])
            ),
            None,
        )
        if start is None:
            anomalies.append(
                {"page": lines[esp_idx][0], "issue": f"início da tradição '{name}' não encontrado"}
            )
            start = prev_bound
        if novato_idx is None:
            anomalies.append(
                {"page": lines[esp_idx][0], "issue": f"header 'Novato de {name}' não encontrado"}
            )
        mestre_idx = next(
            (i for i, r, n in headers if r == "mestre" and n == name), esp_idx
        )
        sections.append((start, name, "intro"))
        if novato_idx is not None:
            sections.append((novato_idx, name, "novato"))
        sections.append((esp_idx, name, "especialista"))
        sections.append((mestre_idx, name, "mestre"))
        prev_bound = mestre_idx
    return sections, anomalies


def clean_intro(
    raw: list[str], own: str, names: set[str], anomalies: list[dict], page: int
) -> list[str]:
    """Strip chapter-index table rows interleaved into a tradition intro."""
    out: list[str] = []
    skip_next_short = False
    for line in raw:
        s = line.strip()
        if skip_next_short:
            skip_next_short = False
            if len(s) < 45 and not s.endswith("."):
                continue
        if s in TABLE_FURNITURE or s == "**Tradição Descrição.**":
            anomalies.append(
                {"page": page, "issue": f"linha de tabela removida da intro de '{own}': '{s}'"}
            )
            continue
        if s in names and s != own:
            skip_next_short = True
            anomalies.append(
                {"page": page, "issue": f"linha de tabela removida da intro de '{own}': '{s}'"}
            )
            continue
        out.append(s)
    return out


def parse(lines: list[tuple[int, str]]) -> tuple[list[Tradition], list[Spell], list[dict]]:
    sections, anomalies = find_sections(lines)
    traditions: list[Tradition] = []
    spells: list[Spell] = []
    all_names = {name for _, name, _ in sections}

    bounds = [s[0] for s in sections] + [len(lines)]
    by_name: dict[str, Tradition] = {}

    for sec_i, (start, name, rank) in enumerate(sections):
        end = bounds[sec_i + 1]
        if name not in by_name:
            by_name[name] = Tradition(name=name, page=lines[start][0])
            traditions.append(by_name[name])
        tradition = by_name[name]

        current_spell: Spell | None = None
        pending_name: tuple[int, str] | None = None  # (page, raw ALL-CAPS name)
        pending_junk: list[str] = []  # stray lines between a name and its stats

        def flush_pending(as_heading: bool) -> None:
            """Fold an unconfirmed caps line (+trailing lines) into the context."""
            nonlocal pending_name
            if pending_name is None:
                return
            target = current_spell.body if current_spell else tradition.intro
            if as_heading:
                target.append(f"**{pt_title(pending_name[1])}.**")
            target.extend(pending_junk)
            pending_name = None
            pending_junk.clear()

        # Skip the boundary line itself (tradition heading or rank header).
        for page, line in lines[start + 1 : end]:
            stripped = line.strip()
            if not stripped:
                continue

            sm = STAT_RE.match(stripped)
            if sm:
                key = {"CONJURAÇÕES": "conjuracoes", "ALVO": "alvo", "DURAÇÃO": "duracao"}[
                    sm.group(1)
                ]
                if key == "conjuracoes" and pending_name is not None:
                    name_page, raw_name = pending_name
                    current_spell = Spell(
                        name=pt_title(raw_name), tradition=name, rank=rank, page=name_page
                    )
                    spells.append(current_spell)
                    for junk in pending_junk:
                        anomalies.append(
                            {
                                "page": name_page,
                                "issue": f"linha descartada entre nome e stats de '{current_spell.name}': '{junk}'",
                            }
                        )
                    pending_name = None
                    pending_junk.clear()
                if current_spell is not None:
                    value = sm.group(2).strip()
                    current_spell.stats[key] = (
                        int(value) if key == "conjuracoes" and value.isdigit() else value
                    )
                else:
                    anomalies.append(
                        {"page": page, "issue": f"linha de stat órfã: '{stripped}'"}
                    )
                continue

            if is_all_caps_name(stripped):
                if pending_name is not None and not pending_junk:
                    # Wrapped name: 'ZUMBIDO' / 'DA HOSTE' → merge.
                    pending_name = (pending_name[0], f"{pending_name[1]} {stripped}")
                else:
                    flush_pending(as_heading=True)
                    pending_name = (page, stripped)
                continue

            # Regular text. Tolerate a little page-furniture noise between a
            # spell name and its stats; past that, the caps line was a
            # sidebar/table heading — fold it so no content is lost.
            if pending_name is not None:
                pending_junk.append(stripped)
                if len(pending_junk) > 2:
                    flush_pending(as_heading=True)
                continue
            (current_spell.body if current_spell else tradition.intro).append(stripped)

        flush_pending(as_heading=True)

    for tradition in traditions:
        tradition.intro = clean_intro(
            tradition.intro, tradition.name, all_names, anomalies, tradition.page
        )

    return traditions, spells, anomalies


def first_sentence(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    m = re.match(r"(.+?[.!?])\s", text + " ")
    s = m.group(1) if m else text
    return (s[: limit - 1] + "…") if len(s) > limit else s


def to_paragraphs(lines: list[str]) -> str:
    return " ".join(" ".join(lines).split())


def render_spell(spell: Spell) -> str:
    body = to_paragraphs(spell.body)
    summary = first_sentence(body) if body else f"Feitiço de {spell.tradition}."
    tags = [slugify(spell.tradition), spell.rank]
    stats_lines = [f'  tradicao: "{spell.tradition}"', f'  rank: "{spell.rank.capitalize()}"']
    for key in ("conjuracoes", "alvo", "duracao"):
        if key in spell.stats:
            v = spell.stats[key]
            stats_lines.append(f"  {key}: {v}" if isinstance(v, int) else f'  {key}: "{v}"')
    return (
        "---\n"
        f'title: "{spell.name}"\n'
        'category: "magias"\n'
        f'summary: "{summary.replace(chr(34), chr(39))}"\n'
        f"tags: [{', '.join(repr(t) for t in tags)}]\n"
        "stats:\n" + "\n".join(stats_lines) + "\n"
        "source:\n"
        '  book: "livro-basico"\n'
        f"  page: {spell.page}\n"
        "---\n\n"
        f"{body}\n"
    )


def render_tradition(trad: Tradition) -> str:
    body = to_paragraphs(trad.intro)
    summary = first_sentence(body) if body else f"A tradição de {trad.name}."
    return (
        "---\n"
        f'title: "{trad.name} (Tradição)"\n'
        'category: "magias"\n'
        f'summary: "{summary.replace(chr(34), chr(39))}"\n'
        f"tags: ['tradicao', {slugify(trad.name)!r}]\n"
        "stats:\n"
        f'  tradicao: "{trad.name}"\n'
        '  rank: "Tradição"\n'
        "source:\n"
        '  book: "livro-basico"\n'
        f"  page: {trad.page}\n"
        "---\n\n"
        f"{body}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=Path(".tmp/extracted/livro-basico"))
    parser.add_argument("--out", type=Path, default=Path("src/content/codex/magias"))
    args = parser.parse_args()

    lines = load_lines(args.src)
    traditions, spells, anomalies = parse(lines)

    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("*.md"):
        old.unlink()

    used: dict[str, Spell] = {}
    for spell in spells:
        slug = slugify(spell.name)
        if slug in used:
            slug = f"{slug}-{slugify(spell.tradition)}"
        if slug in used:
            anomalies.append(
                {"page": spell.page, "issue": f"colisão de slug irrecuperável: {slug}"}
            )
            continue
        used[slug] = spell
        if not spell.body:
            anomalies.append({"page": spell.page, "issue": f"feitiço sem corpo: '{spell.name}'"})
        (args.out / f"{slug}.md").write_text(render_spell(spell), encoding="utf-8")

    for trad in traditions:
        slug = f"tradicao-{slugify(trad.name)}"
        (args.out / f"{slug}.md").write_text(render_tradition(trad), encoding="utf-8")
        if not trad.intro:
            anomalies.append({"page": trad.page, "issue": f"tradição sem intro: '{trad.name}'"})

    report = {
        "spells": len(spells),
        "traditions": len(traditions),
        "per_rank": {
            r: sum(1 for s in spells if s.rank == r)
            for r in ("intro", "novato", "especialista", "mestre")
        },
        "anomalies": anomalies,
    }
    Path(".tmp/spell-parse-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"OK: {len(spells)} feitiços + {len(traditions)} tradições → {args.out} "
        f"({len(anomalies)} anomalia(s) em .tmp/spell-parse-report.json)"
    )


if __name__ == "__main__":
    main()
