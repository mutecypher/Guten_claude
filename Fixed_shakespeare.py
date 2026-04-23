#!/usr/bin/env python3
"""
Find correct Gutenberg IDs for Shakespeare plays and download them
with GB prefix to avoid filename collisions.
"""
import re
import time
import urllib.request
import json
from pathlib import Path

BOOKS_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")

START_RE = re.compile(
    r"\*{3}\s*START OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE,
)
END_RE = re.compile(
    r"\*{3}\s*END OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE,
)

# Plays we need to find and download correctly
# (search_term, expected_filename)
NEEDED_PLAYS = [
    ("henry IV part 1 shakespeare",  "GB_HENRY_IV_PART_1.txt"),
    ("henry IV part 2 shakespeare",  "GB_HENRY_IV_PART_2.txt"),
    ("henry V shakespeare",          "GB_HENRY_V.txt"),
    ("henry VI part 1 shakespeare",  "GB_HENRY_VI_PART_1.txt"),
    ("henry VI part 2 shakespeare",  "GB_HENRY_VI_PART_2.txt"),
    ("henry VI part 3 shakespeare",  "GB_HENRY_VI_PART_3.txt"),
    ("richard III shakespeare",      "GB_RICHARD_III.txt"),
    ("king john shakespeare",        "GB_KING_JOHN.txt"),
    ("troilus cressida shakespeare", "GB_TROILUS_AND_CRESSIDA.txt"),
    ("timon athens shakespeare",     "GB_TIMON_OF_ATHENS.txt"),
    ("titus andronicus shakespeare", "GB_TITUS_ANDRONICUS.txt"),
    ("pericles shakespeare",         "GB_PERICLES.txt"),
    ("cymbeline shakespeare",        "GB_CYMBELINE.txt"),
    ("winters tale shakespeare",     "GB_WINTERS_TALE.txt"),
    ("loves labours lost shakespeare","GB_LOVES_LABOURS_LOST.txt"),
    ("two gentlemen verona shakespeare","GB_TWO_GENTLEMEN_OF_VERONA.txt"),
    ("merry wives windsor shakespeare","GB_MERRY_WIVES_OF_WINDSOR.txt"),
    ("comedy errors shakespeare",    "GB_COMEDY_OF_ERRORS.txt"),
    ("measure for measure shakespeare","GB_MEASURE_FOR_MEASURE.txt"),
    ("taming shrew shakespeare",     "GB_TAMING_OF_THE_SHREW.txt"),
    ("all's well ends well shakespeare","GB_ALLS_WELL_THAT_ENDS_WELL.txt"),
    ("antony cleopatra shakespeare", "GB_ANTONY_AND_CLEOPATRA.txt"),
    ("coriolanus shakespeare",       "GB_CORIOLANUS.txt"),
    ("romeo juliet shakespeare",     "GB_ROMEO_AND_JULIET.txt"),
    ("julius caesar shakespeare",    "GB_JULIUS_CAESAR.txt"),
    ("twelfth night shakespeare",    "GB_TWELFTH_NIGHT.txt"),
    ("much ado nothing shakespeare", "GB_MUCH_ADO_ABOUT_NOTHING.txt"),
    ("as you like it shakespeare",   "GB_AS_YOU_LIKE_IT.txt"),
    ("merchant venice shakespeare",  "GB_MERCHANT_OF_VENICE.txt"),
    ("midsummer nights dream shakespeare","GB_MIDSUMMER_NIGHTS_DREAM.txt"),
]

def search_gutendex(query: str) -> list:
    """Search Gutendex for a book."""
    q = query.replace(" ", "+")
    url = f"https://gutendex.com/books/?search={q}&languages=en"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
    return data.get("results", [])

def find_shakespeare_id(query: str) -> tuple[int, str] | None:
    """Find the Gutenberg ID for a Shakespeare play."""
    results = search_gutendex(query)
    for book in results:
        author = book["authors"][0]["name"] if book["authors"] else ""
        if "shakespeare" in author.lower():
            return book["id"], book["title"]
    return None

def download_book(book_id: int, filename: str) -> bool:
    """Download and extract a book from Gutenberg."""
    out_path = BOOKS_DIR / filename
    if out_path.exists():
        print(f"  Already exists: {filename}")
        return True

    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    print(f"  Downloading {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
        start_match = START_RE.search(raw)
        if not start_match:
            print(f"  No START/END markers found")
            return False
        body_start = start_match.end()
        end_match = END_RE.search(raw, body_start)
        body_end = end_match.start() if end_match else len(raw)
        body = raw[body_start:body_end].strip()
        out_path.write_text(body, encoding="utf-8")
        print(f"  Saved {out_path.stat().st_size // 1024:,} KB")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print("Finding correct Gutenberg IDs for Shakespeare plays...\n")

    found = []
    not_found = []

    for query, filename in NEEDED_PLAYS:
        print(f"Searching: {query}")
        result = find_shakespeare_id(query)
        if result:
            book_id, title = result
            print(f"  Found ID {book_id}: {title}")
            found.append((book_id, filename, title))
        else:
            print(f"  NOT FOUND")
            not_found.append(query)
        time.sleep(0.5)

    print(f"\nFound {len(found)}/{len(NEEDED_PLAYS)} plays")
    if not_found:
        print(f"Not found: {not_found}")

    answer = input(f"\nDownload {len(found)} plays? (yes/no): ")
    if answer.strip().lower() != "yes":
        print("Aborted.")
        return

    succeeded = []
    failed = []

    for book_id, filename, title in found:
        print(f"\n[{book_id}] {title} → {filename}")
        if download_book(book_id, filename):
            succeeded.append(filename)
        else:
            failed.append(filename)
        time.sleep(2)

    print(f"\nDownloaded: {len(succeeded)}/{len(found)}")
    if failed:
        print(f"Failed: {failed}")

    # Verify contents
    print("\nVerifying downloaded files:")
    for filename in succeeded:
        path = BOOKS_DIR / filename
        if path.exists():
            first_line = path.read_text(
                encoding="utf-8", errors="replace"
            ).split("\n")[0].strip()
            print(f"  {filename}: {first_line[:60]}")

if __name__ == "__main__":
    main()