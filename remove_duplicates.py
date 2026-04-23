#!/usr/bin/env python3
"""
Smart deduplication for Gutenberg books.
- Detects periodicals (magazines, journals) by title pattern and protects them
- For remaining title-groups, compares content via hashing and keeps the longest
  unique version, discarding only near-identical duplicates.
"""

import re
import hashlib
from pathlib import Path
from collections import defaultdict

BOOKS_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")
REVIEW_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/dedup_review")
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Patterns that suggest a periodical rather than a book/play.
# Add more as you discover them in your corpus.
# ------------------------------------------------------------------
PERIODICAL_PATTERNS = [
    r"scientific.?american",
    r"harper.?s",
    r"atlantic.?monthly",
    r"blackwood",
    r"punch",
    r"strand.?magazine",
    r"cornhill",
    r"chambers",
    r"scribner",
    r"century.?magazine",
    r"galaxy.?magazine",
    r"lippincott",
    r"godey",
    r"littell",
    r"living.?age",
    r"all.?the.?year.?round",
    r"household.?words",
    r"once.?a.?week",
    r"magazine",
    r"journal",
    r"review",
    r"quarterly",
    r"bulletin",
    r"proceedings",
    r"transactions",
    r"digest",
    r"weekly",
    r"monthly",
    r"annual",
    r"almanac",
    r"gazette",
    r"chronicle",
    r"newsletter",
]

PERIODICAL_RE = re.compile(
    "|".join(PERIODICAL_PATTERNS),
    re.IGNORECASE,
)

def is_periodical(title: str) -> bool:
    return bool(PERIODICAL_RE.search(title))

def strip_id(filename: str) -> str:
    """Remove the leading 00001_ numeric prefix to get the bare title."""
    return "_".join(Path(filename).stem.split("_")[1:])

def content_fingerprint(path: Path, sample_size: int = 8192) -> str:
    """
    Hash the first + middle + last bytes of the file for a fast
    near-duplicate fingerprint without reading the whole file.
    """
    size = path.stat().st_size
    text = path.read_bytes()
    # Take three samples: start, middle, end
    mid = max(0, (size // 2) - (sample_size // 2))
    end = max(0, size - sample_size)
    sample = (
        text[:sample_size] +
        text[mid:mid + sample_size] +
        text[end:]
    )
    return hashlib.md5(sample).hexdigest()

def main():
    all_files = sorted(BOOKS_DIR.glob("*.txt"))
    print(f"Total files: {len(all_files):,}")

    periodicals = []
    books = []

    for f in all_files:
        title = strip_id(f.name)
        if is_periodical(title):
            periodicals.append(f)
        else:
            books.append(f)

    print(f"  Periodicals (protected): {len(periodicals):,}")
    print(f"  Books/plays (dedup candidates): {len(books):,}")

    # Group books by title
    by_title = defaultdict(list)
    for f in books:
        title = strip_id(f.name)
        by_title[title].append(f)

    solo = sum(1 for v in by_title.values() if len(v) == 1)
    groups = {k: v for k, v in by_title.items() if len(v) > 1}
    print(f"  Unique titles (no duplicates): {solo:,}")
    print(f"  Title groups with duplicates: {len(groups):,}")

    to_delete = []
    uncertain = []  # groups where content differs significantly

    for title, files in groups.items():
        # Fingerprint each file
        fingerprints = {}
        for f in files:
            fingerprints[f] = content_fingerprint(f)

        # Group by fingerprint — identical fingerprint = true duplicate
        fp_groups = defaultdict(list)
        for f, fp in fingerprints.items():
            fp_groups[fp].append(f)

        if len(fp_groups) == 1:
            # All copies are identical — keep the largest, delete the rest
            by_size = sorted(files, key=lambda f: f.stat().st_size, reverse=True)
            to_delete.extend(by_size[1:])

        elif len(fp_groups) == len(files):
            # Every copy has a different fingerprint — content is genuinely different
            # Flag for manual review rather than auto-deleting
            uncertain.append((title, files))

        else:
            # Mixed: some identical, some different
            # Within each fingerprint group, keep largest; flag cross-group for review
            for fp, fp_files in fp_groups.items():
                if len(fp_files) > 1:
                    by_size = sorted(fp_files, key=lambda f: f.stat().st_size, reverse=True)
                    to_delete.extend(by_size[1:])
            if len(fp_groups) > 1:
                # Different versions exist — flag for review
                surviving = [
                    sorted(fp_files, key=lambda f: f.stat().st_size, reverse=True)[0]
                    for fp_files in fp_groups.values()
                ]
                uncertain.append((title, surviving))

    # Write review report
    report_path = REVIEW_DIR / "uncertain_duplicates.txt"
    with open(report_path, "w") as report:
        report.write(f"TITLES WITH DIFFERING VERSIONS — MANUAL REVIEW NEEDED\n")
        report.write(f"{'='*60}\n\n")
        for title, files in uncertain:
            report.write(f"Title: {title}\n")
            for f in files:
                size_kb = f.stat().st_size // 1024
                report.write(f"  {size_kb:>6} KB  {f.name}\n")
            report.write("\n")

    print(f"\nReady to delete {len(to_delete):,} exact duplicates")
    print(f"Flagged {len(uncertain):,} title groups with differing versions")
    print(f"Review report written to: {report_path}")

    if to_delete:
        answer = input(f"\nDelete {len(to_delete):,} exact duplicates? (yes/no): ")
        if answer.strip().lower() == "yes":
            for f in to_delete:
                print(f"  Deleting: {f.name}")
                f.unlink()
            print(f"Done. Deleted {len(to_delete):,} files.")
        else:
            print("Aborted — nothing deleted.")

    print(f"\nPeriodicals were left untouched ({len(periodicals):,} files).")
    print(f"Check {report_path} for titles needing manual review.")

if __name__ == "__main__":
    main()