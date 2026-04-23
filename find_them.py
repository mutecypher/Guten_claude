#!/usr/bin/env python3
"""
Find extracted book files by searching file contents for author names,
since titles may not match expected strings.
"""
from pathlib import Path

BOOKS_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")

# Author → what we're looking for
targets = {
    "mark twain":       "Twain (Huck Finn / Tom Sawyer)",
    "tolstoy":          "Tolstoy (Anna Karenina)",
    "dostoevsky":       "Dostoevsky (Brother Karamazov)",
    "victor hugo":      "Hugo (Les Misérables / Hunchback)",
    "alexandre dumas":  "Dumas (Monte Cristo / Three Musketeers)",
    "charlotte bront":  "Charlotte Brontë (Jane Eyre)",
    "george eliot":     "George Eliot (Middlemarch)",
    "hawthorne":        "Hawthorne (Scarlet Letter)",
    "lewis carroll":    "Carroll (Looking Glass / Snark)",
    "edward lear":      "Lear (Owl and Pussycat)",
}

found = {t: [] for t in targets}
all_books = sorted(BOOKS_DIR.glob("*.txt"))
total = len(all_books)

print(f"Searching {total:,} extracted book files...")
for i, book_path in enumerate(all_books):
    if i % 1000 == 0:
        print(f"  {i:,}/{total:,}", end="\r")
    try:
        # Only read first 500 chars — fast and sufficient for header info
        sample = book_path.read_text(encoding="utf-8", errors="replace")[:500].lower()
        for author in targets:
            if author in sample:
                found[author].append(book_path.name)
    except Exception:
        continue

print(f"\n\nExtracted files by author:")
for author, files in sorted(found.items(), key=lambda x: targets[x[0]]):
    label = targets[author]
    if files:
        print(f"\n  ✓ {label}:")
        for f in files:
            print(f"      {f}")
    else:
        print(f"\n  ✗ NOT EXTRACTED: {label}")
        print(f"      → may need manual download or re-extraction")