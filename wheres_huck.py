#!/usr/bin/env python3
"""
Search parquet files more flexibly for suspected missing books
using author names rather than titles.
"""
import pyarrow.parquet as pq
from pathlib import Path

PARQUET_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_parquet")
parquet_files = sorted(PARQUET_DIR.glob("data/en*.parquet"))

# Search by author name instead of title for better recall
targets = {
    "twain":          "Twain (Huck Finn / Tom Sawyer)",
    "tolstoy":        "Tolstoy (Anna Karenina)",
    "dostoevsky":     "Dostoevsky (Brother Karamazov)",
    "hugo":           "Hugo (Les Misérables / Hunchback)",
    "dumas":          "Dumas (Monte Cristo / Three Musketeers)",
    "charlotte bront":"Charlotte Brontë (Jane Eyre)",
    "george eliot":   "George Eliot (Middlemarch)",
    "hawthorne":      "Hawthorne (Scarlet Letter)",
    "carroll":        "Carroll (Looking Glass / Snark)",
    "lear":           "Lear (Owl and Pussycat)",
    "james":          "Henry James (Golden Bowl)",
    "william james":  "William James (Varieties)",
}

found = {t: [] for t in targets}

print(f"Searching {len(parquet_files)} shards by author...")
for i, shard_path in enumerate(parquet_files):
    print(f"  Shard {i+1}/{len(parquet_files)}", end="\r")
    table = pq.read_table(shard_path, columns=["text"])
    for text in table.column("text").to_pylist():
        if not text:
            continue
        lower = text.lower()[:500]
        for author in targets:
            if author in lower and shard_path.name not in found[author]:
                found[author].append(shard_path.name)

print("\n\nResults by author:")
for author, shards in sorted(found.items()):
    label = targets[author]
    if shards:
        print(f"  ✓ FOUND  {label}")
    else:
        print(f"  ✗ MISSING  {label}")