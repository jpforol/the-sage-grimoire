#!/usr/bin/env python3
"""Parse the expert/master path chapters into trilhas entries.

Deterministic implementation of specs/path-parser.md:
    python tools/parse_paths.py [--src .tmp/extracted/livro-basico]

Especialista: file pages 166-199 (levels 3/4/6/9). Mestre: 200-279 (7/8/10).
Anomaly report at .tmp/path-parse-report.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_entries import slugify
from parse_ancestries import FURNITURE_RE, first_sentence, reflow, render

LEVEL_RE = re.compile(r"^([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w Áá-úÀ-ÿ'’-]{1,38}?) Nível (\d{1,2})\s*$")

# Book-level naming quirks: level headers that disagree with the section heading.
NAME_ALIAS = {
    "Guerreiro Arcano": "Combatente Arcano",  # Nível 9 header misprint (p185)
    "Vanguardista": "Vanguarda",  # heading is the noun, headers the adjective (p213)
}

RANGES = {
    "especialista": (166, 199),
    "mestre": (200, 279),
}


def load_lines(src: Path, lo: int, hi: int) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for n in range(lo, hi + 1):
        path = src / f"page-{n:03d}.txt"
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not FURNITURE_RE.match(raw.strip()):
                lines.append((n - 1, raw.rstrip()))  # book page = file page - 1
    return lines


def parse_region(
    lines: list[tuple[int, str]], anomalies: list[dict]
) -> list[dict]:
    """Return [{name, page, intro, levels: [(n, lines)]}] for one chapter."""
    headers: list[tuple[int, str, str]] = []  # (line idx, name, level)
    for i, (_, line) in enumerate(lines):
        m = LEVEL_RE.match(line.strip())
        if m:
            headers.append((i, NAME_ALIAS.get(m.group(1), m.group(1)), m.group(2)))

    order: list[str] = []
    counts: dict[str, int] = {}
    for _, name, _ in headers:
        counts[name] = counts.get(name, 0) + 1
        if name not in order:
            order.append(name)

    valid = [n for n in order if counts[n] >= 2]
    for n in order:
        if counts[n] < 2:
            idx = next(i for i, nm, _ in headers if nm == n)
            anomalies.append(
                {
                    "page": lines[idx][0],
                    "issue": f"header de nível único ignorado: '{lines[idx][1].strip()}'",
                }
            )

    paths: list[dict] = []
    prev_bound = 0
    for name in valid:
        first_idx = next(i for i, nm, _ in headers if nm == name)
        start = next(
            (
                i
                for i in range(first_idx - 1, prev_bound - 1, -1)
                if lines[i][1].strip() == name
            ),
            None,
        )
        heading_lines = 1
        if start is None:
            # Wrapped heading: 'Portador da' / 'Lâmina Negra' on two lines.
            start = next(
                (
                    i
                    for i in range(first_idx - 2, prev_bound - 1, -1)
                    if f"{lines[i][1].strip()} {lines[i + 1][1].strip()}" == name
                ),
                None,
            )
            heading_lines = 2
        if start is None:
            anomalies.append(
                {"page": lines[first_idx][0], "issue": f"início da trilha '{name}' não encontrado"}
            )
            start = first_idx
            heading_lines = 1
        paths.append(
            {"name": name, "start": start, "heading_lines": heading_lines}
        )
        prev_bound = first_idx

    # Resolve boundaries: each path ends where the next one starts.
    results: list[dict] = []
    for i, p in enumerate(paths):
        end = paths[i + 1]["start"] if i + 1 < len(paths) else len(lines)
        name = p["name"]
        page = lines[p["start"]][0]
        intro: list[str] = []
        levels: list[tuple[str, list[str]]] = []
        current: list[str] | None = None
        for book_page, line in lines[p["start"] + p["heading_lines"] : end]:
            s = line.strip()
            m = LEVEL_RE.match(s)
            if m and NAME_ALIAS.get(m.group(1), m.group(1)) == name:
                current = []
                levels.append((m.group(2), current))
                continue
            (current if current is not None else intro).append(s)
        results.append({"name": name, "page": page, "intro": intro, "levels": levels})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=Path(".tmp/extracted/livro-basico"))
    parser.add_argument("--out", type=Path, default=Path("src/content/codex"))
    args = parser.parse_args()

    anomalies: list[dict] = []
    tri_dir = args.out / "trilhas"
    tri_dir.mkdir(parents=True, exist_ok=True)

    # Idempotency: remove previously generated especialista/mestre entries.
    for old in tri_dir.glob("*.md"):
        head = old.read_text(encoding="utf-8")[:300]
        if 'subcategory: "especialista"' in head or 'subcategory: "mestre"' in head:
            old.unlink()

    # Existing slugs across the whole collection (for collision suffixing).
    existing = {f.stem for f in args.out.rglob("*.md")}

    counts: dict[str, int] = {}
    for subcategory, (lo, hi) in RANGES.items():
        lines = load_lines(args.src, lo, hi)
        paths = parse_region(lines, anomalies)
        counts[subcategory] = len(paths)

        for p in paths:
            body_parts = [reflow(p["intro"])]
            for level, level_lines in p["levels"]:
                body_parts.append(f"## Nível {level}\n\n{reflow(level_lines)}")
            body = "\n\n".join(part for part in body_parts if part.strip())

            summary = first_sentence(reflow(p["intro"], bold_leads=False)) or (
                f"Trilha de {subcategory} — níveis "
                + ", ".join(lv for lv, _ in p["levels"])
                + "."
            )
            if summary.startswith("##"):
                summary = f"Trilha de {subcategory}: {p['name']}."

            slug = slugify(p["name"])
            if slug in existing:
                slug = f"{slug}-trilha"
            if slug in existing:
                anomalies.append(
                    {"page": p["page"], "issue": f"colisão de slug irrecuperável: {slug}"}
                )
                continue
            existing.add(slug)

            entry = render(
                {
                    "title": p["name"],
                    "category": "trilhas",
                    "subcategory": subcategory,
                    "summary": summary,
                    "tags": [subcategory],
                    "source": {"book": "livro-basico", "page": p["page"]},
                },
                body,
            )
            (tri_dir / f"{slug}.md").write_text(entry, encoding="utf-8")

    report = {"paths": counts, "anomalies": anomalies}
    Path(".tmp/path-parse-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"OK: trilhas {counts} ({len(anomalies)} anomalia(s))")


if __name__ == "__main__":
    main()
