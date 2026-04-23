#!/usr/bin/env python3
import re, time, urllib.request
from pathlib import Path

BOOKS_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")

START_RE = re.compile(
    r"\*{3}\s*START OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE
)
END_RE = re.compile(
    r"\*{3}\s*END OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE
)

BOOKS = [
    (1510, "GB_LOVES_LABOURS_LOST.txt"),
    (1514, "GB_MIDSUMMER_NIGHTS_DREAM.txt"),
    (1539, "GB_WINTERS_TALE.txt"),
    (1542, "GB_TWO_NOBLE_KINSMEN.txt"),   # bonus — co-written with Fletcher
    (1543, "GB_A_LOVERS_COMPLAINT.txt"),  # bonus — Shakespeare poem
    (1544, "GB_THE_PASSIONATE_PILGRIM.txt"), # bonus — Shakespeare poems
]

for book_id, filename in BOOKS:
    out_path = BOOKS_DIR / filename
    if out_path.exists():
        print(f"Already exists: {filename}")
        continue
    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    print(f"Downloading [{book_id}] {filename}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", errors="replace")
        start_match = START_RE.search(raw)
        if not start_match:
            print("  No markers found")
            continue
        body = raw[start_match.end():]
        end_match = END_RE.search(body)
        if end_match:
            body = body[:end_match.start()]
        out_path.write_text(body.strip(), encoding="utf-8")
        print(f"  Saved {out_path.stat().st_size // 1024:,} KB")
        print(f"  First line: {body.strip().split(chr(10))[0][:60]}")
    except Exception as e:
        print(f"  Error: {e}")
    time.sleep(2)

print("\nDone.")