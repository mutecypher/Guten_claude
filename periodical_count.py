#!/usr/bin/env python3
"""
Count books vs periodicals in the gutenberg_books directory.
"""
import re
from pathlib import Path
from collections import defaultdict

BOOKS_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")

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

def main():
    all_files = sorted(BOOKS_DIR.glob("*.txt"))
    total = len(all_files)

    periodicals = []
    books = []

    for f in all_files:
        # Check title portion only (strip leading ID)
        title = "_".join(f.stem.split("_")[1:])
        if PERIODICAL_RE.search(title):
            periodicals.append(f)
        else:
            books.append(f)

    print(f"Total files:   {total:,}")
    print(f"Periodicals:   {len(periodicals):,}  ({100*len(periodicals)/total:.1f}%)")
    print(f"Books/other:   {len(books):,}  ({100*len(books)/total:.1f}%)")

    # Show which periodical patterns matched most often
    print(f"\nTop periodical patterns matched:")
    pattern_counts = defaultdict(int)
    for f in periodicals:
        title = "_".join(f.stem.split("_")[1:])
        for pattern in PERIODICAL_PATTERNS:
            if re.search(pattern, title, re.IGNORECASE):
                pattern_counts[pattern] += 1
                break  # count each file once, for its first matching pattern

    for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"  {pattern:30s}  {count:,}")

    # Write the books-only list to a file for reference
    out_path = BOOKS_DIR.parent / "books_only_filelist.txt"
    with open(out_path, "w") as f:
        for book in books:
            f.write(book.name + "\n")
    print(f"\nBooks-only filelist written to: {out_path}")

if __name__ == "__main__":
    main()