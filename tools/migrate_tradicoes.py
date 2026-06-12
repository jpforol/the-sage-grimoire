#!/usr/bin/env python3
"""Migrate tradition entries from magias/ to tradicoes/ and update category.

Idempotent: re-running deletes any existing tradicoes/ files first, so every
invocation is a fresh copy from the magias/ source.
"""

from pathlib import Path
import frontmatter
import shutil


def main() -> None:
    src_dir = Path("src/content/codex/magias")
    dst_dir = Path("src/content/codex/tradicoes")

    # Idempotency: remove existing tradicoes/ completely
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for trad_file in sorted(src_dir.glob("tradicao-*.md")):
        # Read the tradition entry
        post = frontmatter.load(trad_file)

        # Update category: magias → tradicoes
        post.metadata["category"] = "tradicoes"

        # New filename: remove the "tradicao-" prefix
        # e.g. tradicao-adivinhacao.md → adivinhacao.md
        new_name = trad_file.name[len("tradicao-"):]
        new_path = dst_dir / new_name

        # Write to the new location
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        count += 1
        print(f"Migrated: {trad_file.name} → {new_path.name}")

    print(f"\nMigrated {count} tradition(s) to {dst_dir}/")


if __name__ == "__main__":
    main()
