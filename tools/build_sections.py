#!/usr/bin/env python3
"""Build prose-chapter entries from tools/data/sections_manifest.json.

Deterministic implementation of specs/section-builder.md:
    python tools/build_sections.py

Reflows page+marker ranges of the extracted LivroBasico into Markdown entries,
reconstructing item tables (PREÇO/REQUISITOS/DANO/TRAÇOS) and roll tables
(D3/D6/D20). Report at .tmp/sections-report.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_entries import slugify
from parse_ancestries import first_sentence, reflow, render

# Running headers/footers are lowercase in the page furniture; the real section
# headings are capitalized — match case-sensitively so headings survive.
# Pure-digit lines are stripped in load_lines only when equal to the page folio,
# so table cells like a damage of '0' or roll keys survive.
FURNITURE_RE = re.compile(
    r"^(Licenciado para .*|Capítulo \d+|criando um personagem|regras do jogo|equipamento|Magia)\s*$"
)
ITEM_TABLE_HEADERS = ["PREÇO", "REQUISITOS", "DANO", "TRAÇOS"]
ITEM_CATEGORY_RE = re.compile(r"^(COMUM|INCOMUM|RARO|RARA|EXÓTICO|EXÓTICA)$")
ROLL_HEADER_RE = re.compile(r"^(D3|D6|D20)$")
ROLL_KEY_RE = re.compile(r"^\d{1,2}\s*([–\-—]\s*\d{1,2})?$")
PRICE_RE = re.compile(r"^(—|\d+\s*p[cpo].*|Variável.*)$", re.IGNORECASE)


def load_lines(src: Path, lo: int, hi: int) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for n in range(lo + 1, hi + 2):  # book page N = file page N+1
        path = src / f"page-{n:03d}.txt"
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if FURNITURE_RE.match(s):
                continue
            if s.isdigit() and int(s) == n - 1:  # page folio
                continue
            lines.append((n - 1, raw.rstrip()))
    return lines


def rebuild_item_tables(lines: list[str], report: list[str]) -> list[str]:
    """Reconstruct 5-column item tables (categoria + PREÇO REQUISITOS DANO TRAÇOS)."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if ITEM_CATEGORY_RE.match(s) and [
            x.strip() for x in lines[i + 1 : i + 5]
        ] == ITEM_TABLE_HEADERS:
            category = s.capitalize()
            out.append("")
            out.append(f"| {category} | Preço | Requisitos | Dano | Traços |")
            out.append("| --- | --- | --- | --- | --- |")
            i += 5
            while i + 4 < len(lines) + 1:
                nxt = lines[i].strip() if i < len(lines) else ""
                if (
                    not nxt
                    or ITEM_CATEGORY_RE.match(nxt)
                    or len(nxt) > 60
                    or i + 3 >= len(lines)
                ):
                    break
                name, price, req, dmg, traits = (
                    lines[i].strip(),
                    lines[i + 1].strip(),
                    lines[i + 2].strip(),
                    lines[i + 3].strip(),
                    lines[i + 4].strip() if i + 4 < len(lines) else "",
                )
                if not PRICE_RE.match(price):
                    if "—" not in name and not ITEM_CATEGORY_RE.match(price):
                        report.append(
                            f"linha de tabela de itens inesperada: '{name} / {price}'"
                        )
                    break
                i += 5
                # Wrapped traits cell: continuation lines until the next row
                # (name followed by a price), category or subtable title.
                while i < len(lines):
                    cont = lines[i].strip()
                    after = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    if (
                        not cont
                        or ITEM_CATEGORY_RE.match(cont)
                        or ("—" in cont and len(cont) > 20)
                        or PRICE_RE.match(after)
                        or len(cont) > 45
                        or (cont.isupper() and len(cont) > 6)
                    ):
                        break
                    traits = f"{traits} {cont}"
                    i += 1
                out.append(f"| {name} | {price} | {req} | {dmg} | {traits} |")
            out.append("")
            continue
        out.append(lines[i])
        i += 1
    return out


def rebuild_roll_tables(lines: list[str], report: list[str]) -> list[str]:
    """Reconstruct roll tables (D3/D6/D20 …), re-sorting interleaved column rows."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if ROLL_HEADER_RE.match(s):
            die = s
            # Consume header block: alternating die/title caps lines.
            j = i + 1
            titles = []
            while j < len(lines) and (
                ROLL_HEADER_RE.match(lines[j].strip())
                or (lines[j].strip().isupper() and len(lines[j].strip()) < 40)
            ):
                if not ROLL_HEADER_RE.match(lines[j].strip()):
                    titles.append(lines[j].strip())
                j += 1
            title = titles[0].title() if titles else "Resultado"
            # Collect (roll, text) pairs, tolerating blank lines between rows.
            rows: list[tuple[int, str, str]] = []
            while j < len(lines):
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j >= len(lines) or not ROLL_KEY_RE.match(lines[j].strip()):
                    break
                key = lines[j].strip()
                j += 1
                text: list[str] = []
                while j < len(lines):
                    nxt = lines[j].strip()
                    if not nxt:
                        # blank: only stop if what follows isn't row continuation
                        k2 = j + 1
                        while k2 < len(lines) and not lines[k2].strip():
                            k2 += 1
                        if k2 >= len(lines) or ROLL_KEY_RE.match(lines[k2].strip()):
                            break
                        j += 1
                        continue
                    if ROLL_KEY_RE.match(nxt) or ROLL_HEADER_RE.match(nxt):
                        break
                    text.append(nxt)
                    j += 1
                first = int(re.match(r"^(\d+)", key).group(1))
                rows.append((first, key, " ".join(" ".join(text).split())))
            if len(rows) >= 2:
                out.append("")
                out.append(f"| {die} | {title} |")
                out.append("| --- | --- |")
                for _, key, text in sorted(rows, key=lambda r: r[0]):
                    out.append(f"| {key} | {text} |")
                out.append("")
                i = j
                continue
            report.append(f"tabela de rolagem não reconstruída perto de '{s}'")
        out.append(lines[i])
        i += 1
    return out


def main() -> None:
    src = Path(".tmp/extracted/livro-basico")
    manifest = json.loads(
        Path("tools/data/sections_manifest.json").read_text(encoding="utf-8")
    )
    out_root = Path("src/content/codex")
    report: dict = {"sections": 0, "issues": []}

    chapters: dict[str, list[tuple[int, str]]] = {
        cat: load_lines(src, lo, hi)
        for cat, (lo, hi) in manifest["chapter_ranges"].items()
    }

    # Clean previously generated section entries (all .md in these categories
    # except hand-written files are regenerated; sections are the only content).
    generated = {}
    for item in manifest["sections"]:
        generated.setdefault(item["category"], []).append(item)

    def find_marker(
        lines: list[tuple[int, str]], page: int, marker: str | None, from_idx: int = 0
    ) -> int | None:
        if marker is None:
            return 0
        for i in range(from_idx, len(lines)):
            if lines[i][1].strip() == marker and abs(lines[i][0] - page) <= 1:
                return i
        return None

    for category, items in generated.items():
        lines = chapters[category]
        out_dir = out_root / category
        out_dir.mkdir(parents=True, exist_ok=True)
        for old in out_dir.glob("*.md"):
            old.unlink()

        starts: list[int] = []
        for item in items:
            idx = find_marker(lines, item["page"], item["marker"])
            if idx is None:
                report["issues"].append(
                    f"{category}: marcador '{item['marker']}' não encontrado (p{item['page']})"
                )
            starts.append(idx)

        for k, item in enumerate(items):
            if starts[k] is None:
                continue
            end_idx = len(lines)
            for nxt in starts[k + 1 :]:
                if nxt is not None and nxt > starts[k]:
                    end_idx = nxt
                    break
            if "end" in item:
                explicit = find_marker(
                    lines, item["end"]["page"], item["end"]["marker"], starts[k]
                )
                if explicit is not None:
                    end_idx = min(end_idx, explicit)

            raw = [ln for _, ln in lines[starts[k] + (0 if item["marker"] is None else 1) : end_idx]]
            raw = rebuild_item_tables(raw, report["issues"])
            raw = rebuild_roll_tables(raw, report["issues"])

            # reflow, but keep reconstructed table lines verbatim
            blocks: list[str] = []
            buffer: list[str] = []
            for ln in raw + [""]:
                if ln.startswith("|") or ln == "":
                    if buffer:
                        blocks.append(reflow(buffer))
                        buffer = []
                    if ln.startswith("|"):
                        blocks.append(ln)
                else:
                    buffer.append(ln)
            body = "\n".join(
                b if b.startswith("|") else f"\n{b}\n" for b in blocks if b.strip()
            )

            page = lines[starts[k]][0]
            entry = render(
                {
                    "title": item["title"],
                    "category": category,
                    "summary": item["summary"],
                    "source": {"book": "livro-basico", "page": page},
                },
                body,
            )
            (out_dir / f"{slugify(item['title'])}.md").write_text(entry, encoding="utf-8")
            report["sections"] += 1

    Path(".tmp/sections-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"OK: {report['sections']} seções ({len(report['issues'])} problema(s))")


if __name__ == "__main__":
    main()
